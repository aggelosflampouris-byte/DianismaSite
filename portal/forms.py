"""
Forms for public portal and contributor interactions.
"""
from django import forms
from adminpanel.models import AuthorApplication, Article, Category
from adminpanel.parsers import (
    validate_document_file,
    validate_image_file,
    extract_document_content,
)


class WriterApplicationForm(forms.ModelForm):
    """Form for community members to apply as Writers."""

    experience_years = forms.IntegerField(
        required=False,
        min_value=0,
        label='Χρόνια εμπειρίας',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. 5'})
    )
    previous_publications = forms.CharField(
        required=False,
        label='Προηγούμενες δημοσιεύσεις / ΜΜΕ',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. Blog, Ακαδημαϊκά άρθρα'})
    )

    class Meta:
        model = AuthorApplication
        fields = [
            'full_name',
            'email',
            'profession',
            'topic_interest',
            'bio',
            'sample_text',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. Αλέξανδρος Γεωργίου', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@domain.com', 'required': True}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. Δικηγόρος, Βιολόγος, Φοιτητής', 'required': True}),
            'topic_interest': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. Πολιτικός Διάλογος & Θεσμοί', 'required': True}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Περιγράψτε με 2-3 παραγράφους το αντικείμενο σας και τις ιδέες σας...', 'required': True}),
            'sample_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Σύντομο δείγμα γραφής ή προσχέδιο άρθρου...'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Store questionnaire answers in JSONField
        exp = self.cleaned_data.get('experience_years')
        pubs = self.cleaned_data.get('previous_publications')
        instance.questionnaire_data = {
            'experience_years': exp,
            'previous_publications': pubs,
        }
        if commit:
            instance.save()
        return instance


class WriterArticleSubmitForm(forms.ModelForm):
    """Form for approved contributors to submit an article."""

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="— Επιλέξτε Κατηγορία —",
        widget=forms.Select(attrs={'class': 'form-control', 'required': True})
    )

    class Meta:
        model = Article
        fields = [
            'title',
            'category',
            'excerpt',
            'pdf_file',
            'content',
            'lead_image_url',
            'lead_image',
            'read_time_minutes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Τίτλος άρθρου...', 'required': True}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Σύντομη περίληψη (lead paragraph)...', 'required': True}),
            'content': forms.Textarea(attrs={'class': 'form-control editor-content', 'rows': 12, 'placeholder': 'Κυρίως κείμενο του άρθρου...'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'}),
            'lead_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'}),
            'lead_image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://images.unsplash.com/...'}),
            'read_time_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60, 'value': 5}),
        }

    def clean_pdf_file(self):
        doc = self.cleaned_data.get('pdf_file')
        if doc:
            is_valid, err_msg, _ = validate_document_file(doc)
            if not is_valid:
                raise forms.ValidationError(err_msg)
        return doc

    def clean_lead_image(self):
        img = self.cleaned_data.get('lead_image')
        if img:
            is_valid, err_msg = validate_image_file(img)
            if not is_valid:
                raise forms.ValidationError(err_msg)
        return img

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get("content")
        pdf_file = cleaned_data.get("pdf_file")

        if pdf_file and not content:
            extracted_html = extract_document_content(pdf_file)
            if extracted_html:
                cleaned_data["content"] = extracted_html
                content = extracted_html

        if not content and not pdf_file:
            raise forms.ValidationError(
                "Είναι υποχρεωτικό να εισάγετε Κυρίως Κείμενο ή να ανεβάσετε Έγγραφο (PDF / Word .docx)."
            )
        return cleaned_data
