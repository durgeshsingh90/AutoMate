import subprocess
import os

def create_django_app():
    app_name = input("Enter the name of the new app: ").strip()

    # Use relative path from current script to the template
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "monkey_app_template")

    if not os.path.isdir(template_path):
        print(f"❌ Template path does not exist: {template_path}")
        return

    command = [
        "django-admin",
        "startapp",
        app_name,
        f"--template={template_path}"
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ App '{app_name}' created successfully using template.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create app '{app_name}': {e}")

if __name__ == "__main__":
    create_django_app()
