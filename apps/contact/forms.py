from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120)
    email = forms.EmailField()
    subject = forms.CharField(max_length=180)
    message = forms.CharField(widget=forms.Textarea)
    company = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = "form-control"
        for field in self.fields.values():
            if field.widget.__class__.__name__ == "HiddenInput":
                continue
            current = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{current} {input_classes}".strip()
        self.fields["name"].widget.attrs.setdefault("placeholder", "Your name")
        self.fields["email"].widget.attrs.setdefault("placeholder", "you@example.com")
        self.fields["subject"].widget.attrs.setdefault("placeholder", "What is this about?")
        self.fields["message"].widget.attrs.setdefault("rows", 3)
        self.fields["message"].widget.attrs.setdefault(
            "placeholder",
            "Tell me about your project or role.",
        )

    def clean_company(self):
        value = self.cleaned_data.get("company", "").strip()
        if value:
            raise forms.ValidationError("Spam detected.")
        return value

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].strip().split())
        if len(name) < 2:
            raise forms.ValidationError("Please provide your full name.")
        if len(name) > 120:
            raise forms.ValidationError("Name is too long.")
        return name

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_subject(self):
        subject = " ".join(self.cleaned_data["subject"].strip().split())
        if len(subject) < 4:
            raise forms.ValidationError("Subject should be at least 4 characters.")
        return subject

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message.split()) < 5:
            raise forms.ValidationError("Please include at least 5 words so I can respond with context.")
        if message.lower().count("http://") + message.lower().count("https://") > 3:
            raise forms.ValidationError("Please reduce the number of links in your message.")
        return message
