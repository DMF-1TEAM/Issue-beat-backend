import logging
from datetime import datetime, timedelta
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import News, SearchHistory
from .services.llm_service import LLMService


logger = logging.getLogger(__name__)

class SearchNewsAPIView(APIView):
    def get(self, request):
        query = request.GET.get('query', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        if not query:
            return Response({'error': '검색어를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. 뉴스 검색
            news_list = News.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).order_by('-date')

            total_count = news_list.count()
            
            # 2. 일별 통계 계산 - 전체 기간
            daily_counts = news_list.values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            daily_counts_dict = {
                item['date'].strftime('%Y-%m-%d'): item['count'] 
                for item in daily_counts
            }

            # 3. 페이지네이션
            paginator = Paginator(news_list, page_size)
            current_page = paginator.page(page)
            
            news_data = [{
                'id': news.id,
                'title': news.title,
                'content': news.content[:200],
                'press': news.press,
                'date': news.date.strftime('%Y-%m-%d') if news.date else None,
                'link': news.link
            } for news in current_page.object_list]

            # 4. LLM 요약 생성
            try:
                if total_count > 0:
                    llm_service = LLMService()
                    summary_data = [
                        {
                            'title': news.title,
                            'content': news.content
                        }
                        for news in news_list[:10]
                    ]
                    summary = llm_service.generate_structured_summary(summary_data)
                    
                    # 요약 결과가 없는 경우 기본값 설정
                    if not summary or not isinstance(summary, dict):
                        summary = {
                            'background': '요약 정보가 없습니다.',
                            'core_content': '요약 정보가 없습니다.',
                            'conclusion': '요약 정보가 없습니다.'
                        }
                else:
                    summary = {
                        'background': '검색 결과가 없습니다.',
                        'core_content': '검색 결과가 없습니다.',
                        'conclusion': '검색 결과가 없습니다.'
                    }
            except Exception as e:
                print(f"Summary generation error: {e}")
                summary = {
                    'background': '요약 생성 중 오류가 발생했습니다.',
                    'core_content': '요약 생성 중 오류가 발생했습니다.',
                    'conclusion': '요약 생성 중 오류가 발생했습니다.'
                }

            return Response({
                'news_list': news_data,
                'total_count': total_count,
                'current_page': page,
                'total_pages': paginator.num_pages,
                'has_next': current_page.has_next(),
                'has_previous': current_page.has_previous(),
                'summary': summary,
                'daily_counts': daily_counts_dict
            })

        except Exception as e:
            print(f"Search API error: {e}")
            return Response(
                {'error': '검색 중 오류가 발생했습니다.', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetNewsSummaryView(APIView):
    def get(self, request, date=None):
        try:
            if not date:
                latest_news = News.objects.order_by('-date').first()
                if latest_news:
                    date = latest_news.date

            news_data = News.objects.filter(date=date).values('title', 'content')[:10]
            if not news_data:
                return Response({'error': '해당 날짜의 뉴스를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

            llm_service = LLMService()
            summary = llm_service.generate_structured_summary(news_data)

            return Response({
                'success': True,
                'data': summary
            })

        except Exception as e:
            print(f"Error in GetNewsSummaryView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_trending_keywords_api(request):
    trending = cache.get('trending_keywords') or {}
    return JsonResponse({
        'keywords': [{'keyword': k, 'count': v} for k, v in trending.items()]
    })

@api_view(['GET'])
def get_search_suggestions_api(request):
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    suggestions = News.objects.filter(
        Q(keyword__icontains=query) | Q(title__icontains=query)
    ).values_list('keyword', flat=True).distinct()[:5]

    return JsonResponse({'suggestions': list(suggestions)})

@api_view(['GET'])
def get_news_by_date(request, date):
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    try:
        news_list = News.objects.filter(date=date).order_by('-press')
        total_count = news_list.count()
        paginator = Paginator(news_list, page_size)
        current_page = paginator.page(page)

        news_data = [{
            'id': news.id,
            'title': news.title,
            'content': news.content,
            'press': news.press,
            'date': news.date.strftime('%Y-%m-%d'),
            'link': news.link
        } for news in current_page.object_list]

        return Response({
            'news_list': news_data,
            'total_count': total_count,
            'current_page': page,
            'total_pages': paginator.num_pages,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous()
        })

    except Exception as e:
        print(f"Error in get_news_by_date: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_daily_summary(request, date):
    try:
        news_list = News.objects.filter(date=date).values('title', 'content', 'press', 'link')
        if not news_list:
            return Response({'error': '해당 날짜의 뉴스가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        llm_service = LLMService()
        summary = llm_service.generate_structured_summary(news_list)

        return Response({
            'summary': summary,
            'news_list': list(news_list)
        })

    except Exception as e:
        print(f"Error in get_daily_summary: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_daily_stats(request):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    daily_counts = News.objects.filter(
        date__range=(start_date, end_date)
    ).values('date').annotate(count=Count('id')).order_by('date')

    return JsonResponse({'daily_counts': list(daily_counts)})

def home(request):
    """홈 페이지"""
    trending_keywords = []  # 필요한 데이터를 여기에 추가하세요.
    return render(request, 'web/home.html', {'trending_keywords': trending_keywords})

def search_view(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return render(request, 'web/search.html')  # 검색 페이지 템플릿 렌더링

    search_history, created = SearchHistory.objects.get_or_create(
        keyword=query,
        defaults={'count': 1}
    )
    if not created:
        search_history.count += 1
        search_history.save()

    return render(request, 'web/search.html', {'query': query})

