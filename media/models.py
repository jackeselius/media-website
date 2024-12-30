from django.db import models
import os

# Create your models here.

class File(models.Model):
    filename = models.CharField(max_length = 100)
    description = models.CharField(max_length = 1000)
    owner = models.CharField(max_length = 100)
    icon = models.ImageField(upload_to='files/thumbnails', null=True, blank=True)
    #file = models.FileField(upload_to=os.path.join(str(owner), 'videos/'))
    file = models.FileField(upload_to='files/')

    def __str__(self):
        return self.filename

    #def delete(self, *args, **kwargs):
        #print("DELETE MODEL METHOD CALLED")
        #self.file.delete()
        #self.icon.delete()
        #self.filename.delete()
        #self.description.delete()
        #self.owner.delete()
        #super().delete(*args, **kwargs)

    def delete(self, *args, **kwargs):
        #print("DELETE MODEL METHOD CALLED")
        self.file.delete()
        self.icon.delete()
        super().delete(*args, **kwargs)


#beta
# class Video(models.Model):
#     title = models.CharField(max_length = 100)
#     author = models.CharField(max_length = 100)
#     description = models.CharField(max_length = 1000)
#     owner = models.CharField(max_length = 100)
#     thumbnail = models.ImageField(upload_to='videos/thumbnails', null=True, blank=True)
#     #file = models.FileField(upload_to=os.path.join(str(owner), 'videos/'))
#     file = models.FileField(upload_to='videos/')

#     def __str__(self):
#         return self.title

# class Image(models.Model):
#     title = models.CharField(max_length = 100)
#     author = models.CharField(max_length = 100)
#     description = models.CharField(max_length = 1000)
#     owner = models.CharField(max_length = 100)
#     thumbnail = models.ImageField(upload_to='images/thumbnails', null=True, blank=True)
#     #file = models.FileField(upload_to=os.path.join(str(owner), 'videos/'))
#     file = models.FileField(upload_to='images/')

#     def __str__(self):
#         return self.title
