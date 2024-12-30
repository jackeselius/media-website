from django import forms
from .models import File

class FileForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        self.owner = user
        super(FileForm, self).__init__(*args, **kwargs)
        self.fields['owner'].initial = user
    class Meta:
        model = File    #CAN OVERRITE AND SEND TO MODELS FROM HERE USING USER
        fields = ('filename', 'description', 'owner', 'icon', 'file')

#beta
# class VideoForm(forms.ModelForm):
#     def __init__(self, user, *args, **kwargs):
#         self.owner = user
#         super(VideoForm, self).__init__(*args, **kwargs)
#         self.fields['owner'].initial = user
#     class Meta:
#         model = Video
#         fields = ('title', 'author', 'description', 'owner', 'thumbnail', 'file')

# class ImageForm(forms.ModelForm):
#     def __init__(self, user, *args, **kwargs):
#         self.owner = user
#         super(ImageForm, self).__init__(*args, **kwargs)
#         self.fields['owner'].initial = user
#     class Meta:
#         model = Image
#         fields = ('title', 'author', 'description', 'owner', 'thumbnail', 'file')

    # def save(self, commit=True):
    #     self.owner = self.cleaned_data['owner']
    #     if commit:
    #         self.owner.save()
    #     return self.owner #CAUSES AND ERROR ABOUT STR ATTRIBUTE HAS NO ATTRIBUTE OWNER
    #i think this is because of the save copmmit = false thing so this would elimate the need to save twice in views
