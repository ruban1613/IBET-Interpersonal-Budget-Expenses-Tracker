# Multi-Language Support Implementation TODO

## Completed Tasks
- [x] Added translation imports to student_module/views.py
- [x] Wrapped user-facing strings with _() for translation in student_module/views.py
- [x] Wrapped user-facing strings with _() for translation in individual_module/views.py
- [x] Created language switching API endpoints in core/views.py
- [x] Added language switching URLs to core/urls.py

## Pending Tasks
- [x] Generate translation files using makemessages command
- [x] Compile translation files using compilemessages command
- [ ] Update other module views with translation imports and wrapped strings
- [ ] Add translation imports to serializers
- [ ] Test language switching functionality
- [ ] Update existing i18n tests
- [ ] Add translations for Tamil language in .po files

## Next Steps
1. Run `python manage.py makemessages -a` to extract translatable strings
2. Run `python manage.py compilemessages` to compile .po files
3. Update remaining view files (parent_module, individual_module, etc.)
4. Test the language switching API endpoints
5. Add Tamil translations to the .po files

## API Endpoints Added
- POST /api/set-language/ - Set user's language preference
- GET /api/languages/ - Get list of available languages

## Files Modified
- IBET/student_module/views.py - Added translation imports and wrapped strings
- IBET/core/views.py - Created language switching views
- IBET/core/urls.py - Added language switching URLs
