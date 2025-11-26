from django.contrib import admin
from .models import Profile, Residue, Collection, Reward, UserReward, PointsTransaction

admin.site.register(Profile)
admin.site.register(Residue)
admin.site.register(Collection)
admin.site.register(Reward)
admin.site.register(UserReward)
admin.site.register(PointsTransaction)
