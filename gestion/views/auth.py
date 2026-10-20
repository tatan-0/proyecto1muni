from django.contrib.auth.views import LoginView, LogoutView


login_view = LoginView.as_view(template_name="registration/login.html")
logout_view = LogoutView.as_view()
