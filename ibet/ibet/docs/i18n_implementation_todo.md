# Multi-Language Support Implementation TODO

## Pending Tasks
- [ ] Generate translation files using makemessages command
- [ ] Compile translation files using compilemessages command
- [x] Updated parent_module/views.py with translation imports and wrapped strings
- [ ] Update other module views with translation imports and wrapped strings
- [ ] Add translation imports to serializers
- [ ] Test language switching functionality
- [ ] Update existing i18n tests
- [ ] Add translations for Tamil language in .po files

## Next Steps
1. Run `python manage.py makemessages -a` to extract translatable strings
2. Run `python manage.py compilemessages` to compile .po files
3. Update remaining view files (parent_module, individual_module, couple_module, retiree_module, dailywage_module)
4. Update all serializers with translation imports
5. Test the language switching API endpoints
6. Update core/tests_i18n.py
7. Add Tamil translations to the .po files

## Testing
- Critical-path testing: Test key language switching functionality and basic translations
