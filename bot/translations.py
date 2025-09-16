# Multilingual support for the bot

TRANSLATIONS = {
    'uz': {
        'start_message': "Assalomu alaykum! Magazin tarmoqlarida to'langan cheklar yig'ish botiga xush kelibsiz!",
        'choose_language': "Tilni tanlang 🌍:",
        'language_selected': "Til tanlandi: O'zbekcha",
        'share_contact': "📞 Telefon raqamingizni ulashing",
        'contact_button': "📞 Kontaktni ulashish",
        'registration_complete': "✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!",
        'instagram_username': "📸 Instagram akkauntingizni kiriting (@username formatida):",
        'instagram_follow': "📸 Ushbu Instagram sahifasiga obuna bo'ling:",
        'follow_button': "✅ Obuna bo'ldim",
        'subscription_confirmed': "✅ Obuna tasdiqlandi!",
        'choose_branch': "🏪 Filiallar ro'yxatidan birini tanlang:",
        'send_receipt': "📄 Chekni yuboring (PDF, JPG, PNG formatida, 2MB dan oshmasin):",
        'receipt_received': "✅ Chek qabul qilindi va ko'rib chiqilmoqda",
        'receipt_approved': "✅ Sizning chekingiz tasdiqlandi! Rahmat.",
        'receipt_rejected': "❌ Sizning chekingiz rad etildi.\nSabab: {reason}\nIltimos, yangi chek yuboring.",
        'change_language': "🌐 Tilni o'zgartirish",
        'send_receipt_btn': "📄 Chek yuborish",
        'file_too_large': "❌ Fayl hajmi 2MB dan oshmasin",
        'invalid_file_format': "❌ Noto'g'ri fayl formati. Faqat PDF, JPG, PNG qabul qilinadi",
        'back_to_menu': "🔙 Asosiy menyu",
        'invalid_instagram': "❌ Noto'g'ri Instagram username. @ belgisi bilan boshlang",
        'select_branch_first': "❌ Avval filialni tanlang",
        'unrecognized_message': "❌ Bu xabarni tushunmadim. Iltimos, menyudagi tugmalardan foydalaning yoki /start tugmasini bosing.",
        'registration_incomplete': "❌ Ro'yxatdan o'tish yakunlanmagan. Iltimos, /start buyrug'ini bosing va barcha bosqichlarni bajaring."
    },
    'qq': {
        'start_message': "Assalawma aleykum! Dúkan tarmaqlarında tólengen cheklerdi jıynaw botına xosh keldińiz!",
        'choose_language': "Tildi saylań 🌍:",
        'language_selected': "Til saylandı: Qaraqalpaqsha",
        'share_contact': "📞 Telefon nomerińizdi bólisiń",
        'contact_button': "📞 Kontakt jiberiw",
        'registration_complete': "✅ Dizimnen ótiw sátti tamamlandi!",
        'instagram_username': "📸 Instagram akkauntińizdi kiritiń (@username formatında):",
        'instagram_follow': "📸 Usı Instagram betine jazıliwińiz kerek:",
        'follow_button': "✅ Jazıldım",
        'subscription_confirmed': "✅ Jazılıw tastiyiqlandı!",
        'choose_branch': "🏪 Filiallardıń diziminen birewin saylań:",
        'send_receipt': "📄 Chekti jiberiń (PDF, JPG, PNG formatında, 2MB-dan aspasın):",
        'receipt_received': "✅ Chekińiz qabıl etildi hám qaralıp atır",
        'receipt_approved': "✅ Chekińiz tastiyiqlandı! Raxmet.",
        'receipt_rejected': "❌ Chekińiz qabıl etilmedi.\nSebebi: {reason}\nJańa chek jiberiń.",
        'change_language': "🌐 Tildi ózgertiw",
        'send_receipt_btn': "📄 Chek jiberiw",
        'file_too_large': "❌ Fayl ólshemi 2MB-dan aspawı kerek",
        'invalid_file_format': "❌ Nadurıs fayl formatı. Tek PDF, JPG, PNG qabıl etiledi",
        'back_to_menu': "🔙 Bas menyuǵa qaytıw",
        'invalid_instagram': "❌ Nadurıs Instagram @username. @ belgisi menen baslanıwı kerek",
        'select_branch_first': "❌ Aldın filialdı saylawıńız kerek",
        'unrecognized_message': "❌ Bu xabardı túsinbedim. Menyudağı túymelerdi qollanıń yamasa /start túymesine basıń.",
        'registration_incomplete': "❌ Dizimnen ótiw tamamlanbaǧan. /start buyırığın basıń hám barlıq basqıshladı orınlań."
    }
}

def get_text(key: str, language: str = 'uz', **kwargs) -> str:
    """Get translated text by key and language"""
    text = TRANSLATIONS.get(language, TRANSLATIONS['uz']).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text