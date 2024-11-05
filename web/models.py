from django.db import models
from datetime import datetime

class News(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=100)
    press = models.CharField(max_length=20)
    author = models.CharField(max_length=20)
    content = models.TextField()
    keyword = models.TextField()
    image = models.TextField()
    link = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['date', 'press']),
            models.Index(fields=['date', '-press']),
            models.Index(fields=['keyword']),
            models.Index(fields=['date', 'keyword']),
        ]
        
    @classmethod
    def get_search_index(cls):
        """검색을 위한 인덱스 생성"""
        return {
            'mappings': {
                'properties': {
                    'title': {'type': 'text', 'analyzer': 'korean'},
                    'content': {'type': 'text', 'analyzer': 'korean'},
                    'keyword': {'type': 'keyword'},
                    'date': {'type': 'date'},
                    'press': {'type': 'keyword'}
                }
            }
        }

    def __str__(self):
        return f"[{self.press}] {self.title}"

class SearchHistory(models.Model):
    keyword = models.CharField(max_length=100)
    count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-count']

    def __str__(self):
        return f"{self.keyword} ({self.count})"