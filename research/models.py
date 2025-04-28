from django.db import models
import json
import random
import string

def generate_id():
    """Generate a random ID with a 'research_' prefix"""
    random_digits = ''.join(random.choices(string.digits, k=5))
    return f"research_{random_digits}"

class Research(models.Model):
    """Model for research requests and results"""
    id = models.CharField(primary_key=True, max_length=20, default=generate_id)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    query = models.CharField(max_length=500)
    status = models.CharField(max_length=100, default="processing")
    model = models.CharField(max_length=100, default="gemini-1.5-pro")
    search_model = models.CharField(max_length=100, null=True, blank=True)
    max_searches = models.IntegerField(default=5)
    custom_requirement = models.TextField(blank=True, default="")
    error = models.TextField(blank=True, null=True)
    report = models.TextField(blank=True, null=True)
    
    # Store learnings as JSON
    _learnings = models.TextField(db_column='learnings', blank=True, default="[]") 
    
    def __str__(self):
        return f"{self.id}: {self.query}"
    
    @property
    def learnings(self):
        """Get learnings as a list"""
        if not self._learnings:
            return []
        return json.loads(self._learnings)
    
    @learnings.setter
    def learnings(self, value):
        """Set learnings from a list"""
        if isinstance(value, list):
            self._learnings = json.dumps(value)
        else:
            self._learnings = "[]"
    
    def as_dict(self):
        """Return a dictionary representation for API responses"""
        return {
            'id': self.id,
            'status': self.status,
            'query': self.query,
            'learnings': self.learnings,
            'report': self.report,
            'error': self.error
        } 