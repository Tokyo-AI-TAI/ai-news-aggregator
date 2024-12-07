from django import forms


class AddFeedForm(forms.Form):
    url = forms.URLField(
        required=True,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://example.com/feed.xml",
            }
        ),
        help_text="Enter the direct URL of the RSS feed (must start with http:// or https://)",
    )

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        if not url.startswith(("http://", "https://")):
            raise forms.ValidationError("URL must start with http:// or https://")
        return url
