from django.forms import ModelForm, Textarea
from .models import Post

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["content"]
        widgets = { 
            "content": Textarea(attrs={"cols": 100, "rows": 5})
         }