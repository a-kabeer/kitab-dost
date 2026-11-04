"""
Seed Data for Kitaab Bank
Populates realistic school textbooks for Classes 6, 7, and 8.
Covers English, Urdu, and Sindhi languages across core subjects.
"""

from app.database import get_db

SAMPLE_BOOKS = [
    {
        'book_code': 'KB-BK-000001',
        'title': 'Mathematics for Class 6',
        'author': 'Prof. Dr. M. A. Memon, S. K. Baloch',
        'subject': 'Mathematics',
        'class_grade': 'Class 6',
        'language': 'English',
        'publisher': 'Sindh Textbook Board, Jamshoro',
        'edition_year': 2025,
        'condition_state': 'Good',
        'description': 'Official curriculum textbook covering Sets, Whole Numbers, Integers, Fractions, Decimals, Ratio and Proportion, Financial Arithmetic, Introduction to Algebra, and Basic Geometry.',
        'image_path': 'img/covers/math_class6.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000002',
        'title': 'General Science for Grade 6',
        'author': 'Dr. Tariq Mahmood & Panel',
        'subject': 'General Science',
        'class_grade': 'Class 6',
        'language': 'English',
        'publisher': 'Sindh Textbook Board, Jamshoro',
        'edition_year': 2024,
        'condition_state': 'Like New',
        'description': 'Comprehensive grade 6 science textbook detailing Cellular Organization, Plant and Animal Systems, Photosynthesis and Respiration, Atoms and Molecules, and Energy Resources.',
        'image_path': 'img/covers/science_class6.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000003',
        'title': 'اردو لازمی برائے جماعت ششم',
        'author': 'سید شبیر علی کاظمی و دیگر',
        'subject': 'Urdu',
        'class_grade': 'Class 6',
        'language': 'Urdu',
        'publisher': 'قومی نصاب و درسی کتب کونسل',
        'edition_year': 2025,
        'condition_state': 'Good',
        'description': 'جماعت ششم کے طلباء کے لیے سرکاری اردو درسی کتاب۔ حمد، نعت، اسباق سیرت طیبہ، قومی کہانیاں، نظمیں اور بنیادی گرائمر پر مشتمل مکمل کتاب۔',
        'image_path': 'img/covers/urdu_class6.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000004',
        'title': 'سنڌي سليس درجو ڇھون',
        'author': 'استاد محمد عثمان ۽ ساٿي',
        'subject': 'Sindhi',
        'class_grade': 'Class 6',
        'language': 'Sindhi',
        'publisher': 'سنڌ ٽيڪسٽ بڪ بورڊ، ڄامشورو',
        'edition_year': 2024,
        'condition_state': 'Fair',
        'description': 'سنڌي لازمي مضمون جو درسي ڪتاب برائي ڇھون درجو. حمد، نعت، سنڌ جا تاريخي ماڳ، اخلاقي سبق ۽ بنيادي سنڌي وياڪرڻ شامل آهن.',
        'image_path': 'img/covers/sindhi_class6.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000005',
        'title': 'اسلامیات لازمی برائے جماعت ششم',
        'author': 'مولانا عبدالحمید طارق',
        'subject': 'Islamiat',
        'class_grade': 'Class 6',
        'language': 'Urdu',
        'publisher': 'پنجاب کریکولم اینڈ ٹیکسٹ بک بورڈ',
        'edition_year': 2025,
        'condition_state': 'Like New',
        'description': 'قرآن مجید، ایمانیات و عبادات، سیرت النبی ﷺ، اور حسن اخلاق و معاملات پر مشتمل جامع درسی کتاب۔',
        'image_path': 'img/covers/islamiat_class6.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000006',
        'title': 'Social Studies & Geography 6',
        'author': 'Dr. Farooq Ahmed, M. Saleem',
        'subject': 'Social Studies',
        'class_grade': 'Class 6',
        'language': 'English',
        'publisher': 'PTB & STBB Joint Publication',
        'edition_year': 2024,
        'condition_state': 'Good',
        'description': 'Explores Earth as a planet, maps and globes, ancient Indus Valley civilization, physical landscape of Pakistan, and civic responsibilities for middle schoolers.',
        'image_path': 'img/covers/social_class6.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000007',
        'title': 'ریاضی برائے جماعت ہفتم (اردو میڈیم)',
        'author': 'پروفیسر ارشد مسعود خان',
        'subject': 'Mathematics',
        'class_grade': 'Class 7',
        'language': 'Urdu',
        'publisher': 'سندھ ٹیکسٹ بک بورڈ، جامشورو',
        'edition_year': 2025,
        'condition_state': 'Good',
        'description': 'حقیقی اعداد، مربع اور جذر، الجبری کلیات اور فارمولے، لکیری مساواتیں، اور جیومیٹری کے عملی اصولوں پر مبنی اردو میڈیم کتاب۔',
        'image_path': 'img/covers/math_class7.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000008',
        'title': 'General Science for Grade 7',
        'author': 'Prof. A. R. Qureshi, N. H. Shah',
        'subject': 'General Science',
        'class_grade': 'Class 7',
        'language': 'English',
        'publisher': 'Sindh Textbook Board, Jamshoro',
        'edition_year': 2024,
        'condition_state': 'Fair',
        'description': 'Covers Human Organ Systems, Transport in Humans and Plants, Reproduction in Plants, Environment and Feeding Relationships, Water, and Structure of an Atom.',
        'image_path': 'img/covers/science_class7.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000009',
        'title': 'English Grammar & Reading Skills 7',
        'author': 'Rachel Thorne, Asma Zubair',
        'subject': 'English',
        'class_grade': 'Class 7',
        'language': 'English',
        'publisher': 'Oxford Progressive Curriculum',
        'edition_year': 2025,
        'condition_state': 'Like New',
        'description': 'Advanced tenses, direct and indirect speech, active and passive voice, descriptive essay writing, reading comprehension passages, and formal letter drafting.',
        'image_path': 'img/covers/english_class7.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000010',
        'title': 'سنڌي لازمي درجو ستون',
        'author': 'ڊاڪٽر نواز علي شوق',
        'subject': 'Sindhi',
        'class_grade': 'Class 7',
        'language': 'Sindhi',
        'publisher': 'سنڌ ٽيڪسٽ بڪ بورڊ، ڄامشورو',
        'edition_year': 2024,
        'condition_state': 'Good',
        'description': 'درجو ستين لاءِ سنڌي ٻولي جو اعليٰ معيار وارو ڪتاب. شاهه عبداللطيف ڀٽائي جي شاعري، تاريخي شخصيتون، ماحوليات ۽ سنڌي وياڪرڻ جا اصول.',
        'image_path': 'img/covers/sindhi_class7.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000011',
        'title': 'Computer Education & Digital Literacy 7',
        'author': 'Engr. Kamran Siddiqui',
        'subject': 'Computer Science',
        'class_grade': 'Class 7',
        'language': 'English',
        'publisher': 'National Curriculum Board',
        'edition_year': 2025,
        'condition_state': 'Like New',
        'description': 'Hardware concepts, operating systems, word processing techniques, spreadsheets with formulas, internet safety, and introduction to Scratch visual programming.',
        'image_path': 'img/covers/computer_class7.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000012',
        'title': 'Mathematics for Class 8',
        'author': 'Prof. Dr. M. A. Memon, Z. A. Abbasi',
        'subject': 'Mathematics',
        'class_grade': 'Class 8',
        'language': 'English',
        'publisher': 'Sindh Textbook Board, Jamshoro',
        'edition_year': 2025,
        'condition_state': 'Good',
        'description': 'Final board preparation textbook covering Operations on Sets, Real Numbers, Number Systems, Financial Arithmetic, Polynomials, Factorization, Linear Equations, and Trigonometry.',
        'image_path': 'img/covers/math_class8.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000013',
        'title': 'جنرل سائنس برائے جماعت ہشتم',
        'author': 'ڈاکٹر منور حسین و دیگر',
        'subject': 'General Science',
        'class_grade': 'Class 8',
        'language': 'Urdu',
        'publisher': 'سندھ ٹیکسٹ بک بورڈ، جامشورو',
        'edition_year': 2024,
        'condition_state': 'Good',
        'description': 'انسانی اعصابی نظام، خلیاتی تقسیم، موروثیت کے اصول، بائیوٹیکنالوجی، کیمیائی تعاملات، تیزاب اور اساس، اور حرارت کے اثرات پر مشتمل مفصل نصابی کتاب۔',
        'image_path': 'img/covers/science_class8.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000014',
        'title': 'اردو قواعد و انشاء برائے جماعت ہشتم',
        'author': 'ڈاکٹر وحید قریشی',
        'subject': 'Urdu',
        'class_grade': 'Class 8',
        'language': 'Urdu',
        'publisher': 'پنجاب ٹیکسٹ بک بورڈ، لاہور',
        'edition_year': 2025,
        'condition_state': 'Fair',
        'description': 'اسم معرفہ و نکرہ، تذکیر و تانیث، محاورات و ضرب الامثال، خطوط نویسی، درخواست نویسی، کہانی نویسی اور ادبی مضامین کا مکمل احاطہ۔',
        'image_path': 'img/covers/urdu_class8.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000015',
        'title': 'Computer Science: Algorithms & Python 8',
        'author': 'Faisal Rehman, Sarah Khan',
        'subject': 'Computer Science',
        'class_grade': 'Class 8',
        'language': 'English',
        'publisher': 'Tech School Series Publications',
        'edition_year': 2026,
        'condition_state': 'Like New',
        'description': 'Introduction to computational thinking, flowcharting, pseudocode, basic Python programming syntax, loops, conditionals, and database concepts for junior students.',
        'image_path': 'img/covers/computer_class8.svg',
        'status': 'available',
        'is_approved': 1
    },
    {
        'book_code': 'KB-BK-000016',
        'title': 'سنڌي ٻولي ۽ ادب درجو اٺون',
        'author': 'پروفيسر غلام مصطفيٰ قاسمي',
        'subject': 'Sindhi',
        'class_grade': 'Class 8',
        'language': 'Sindhi',
        'publisher': 'سنڌ ٽيڪسٽ بڪ بورڊ، ڄامشورو',
        'edition_year': 2024,
        'condition_state': 'Good',
        'description': 'اٺين درجي جي ٻارن لاءِ سنڌي درسي ڪتاب. ڪلاسيڪل شاعري، سچل سرمست ۽ سامي جو ڪلام، قومي خدمتون، مضمون نگاري ۽ مڪمل وياڪرڻي ضابطا.',
        'image_path': 'img/covers/sindhi_class8.svg',
        'status': 'available',
        'is_approved': 1
    }
]

def seed_sample_books(app=None):
    """Seed sample books into the database if the catalogue is currently empty."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM books;")
    count = cur.fetchone()[0]

    if count == 0:
        for book in SAMPLE_BOOKS:
            cur.execute(
                """
                INSERT INTO books (
                    book_code, title, author, subject, class_grade, language,
                    publisher, edition_year, condition_state, description,
                    image_path, status, is_approved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    book['book_code'], book['title'], book['author'],
                    book['subject'], book['class_grade'], book['language'],
                    book['publisher'], book['edition_year'], book['condition_state'],
                    book['description'], book['image_path'], book['status'],
                    book['is_approved']
                )
            )
        db.commit()
        return len(SAMPLE_BOOKS)
    return 0

if __name__ == '__main__':
    from app import create_app
    app = create_app('development')
    with app.app_context():
        inserted = seed_sample_books()
        print(f"Sample books seeded: {inserted}")
