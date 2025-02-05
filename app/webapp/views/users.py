from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from app.config.settings import LOGIN_URL
from app.webapp.forms import UserProfileForm
from app.webapp.models.user_profile import UserProfile
from app.webapp.models.utils.constants import PRFL


def logout_view(request):
    logout(request)
    return redirect("webapp:home")


@login_required(login_url=LOGIN_URL)
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("webapp:edit-profile")

    else:
        form = UserProfileForm(instance=user_profile)

    return render(
        request, "admin/forms/profile.html", {"form": form, "title": PRFL.capitalize()}
    )
