from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from users.forms import RegisterUserForm, LoginUserForm, ProfileUserForm


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/registration.html'

    success_url = reverse_lazy('users:login')


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/authorization.html'

    def get_success_url(self):
        return reverse_lazy("football:index")


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileUser, self).get_context_data(**kwargs)
        favorite_teams = self.request.user.favorite_teams.all()

        context['favorite_teams'] = favorite_teams

        return context

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user