from django import forms

from .models import ContactSubmission


class ContactForm(forms.ModelForm):
    company = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "subject": forms.TextInput(attrs={"placeholder": "How can we collaborate?"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Tell me about your project or role."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = (
            "w-full rounded-xl border border-slate-300/80 bg-white/80 px-4 py-3 text-sm text-slate-900 "
            "outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-200"
        )
        for field in self.fields.values():
            current = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{current} {input_classes}".strip()

    def clean_company(self):
        value = self.cleaned_data.get("company", "").strip()
        if value:
            raise forms.ValidationError("Spam detected.")
        return value

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message.split()) < 5:
            raise forms.ValidationError("Please include at least 5 words so I can respond with context.")
        return message
