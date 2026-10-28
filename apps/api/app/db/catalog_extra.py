"""Extra starter courses. `ensure_extra_courses()` adds any that are missing BY TITLE,
so it also works on a database that was already seeded (it never duplicates or edits)."""
from sqlalchemy import select

from app.models.course import Course
from app.models.user import User


def Q(prompt, options, answer, explanation=""):
    return {"prompt": prompt, "options": options, "answer_index": answer, "explanation": explanation}


EXTRA = [
    dict(
        title="English Grammar Essentials",
        description="Nouns, verbs, tenses and punctuation, explained simply with lots of examples.",
        subject="English", level="Beginner", accent="rose",
        curriculum=[
            ("Parts of Speech", [
                ("Nouns and Pronouns", "Naming words and the words that replace them.", 8,
                 "A noun names a person, place, thing or idea, for example teacher, Lagos, book or freedom.\n\n"
                 "A pronoun replaces a noun so we do not repeat it. Instead of saying Ada likes Ada's bag, we say Ada likes her bag.",
                 [Q("Which word is a noun?", ["quickly", "teacher", "run", "beautiful"], 1, "A teacher is a person."),
                  Q("Which pronoun replaces 'Ada' in: Ada left early?", ["She", "It", "They", "We"], 0)]),
                ("Verbs and Adverbs", "Action words and how actions are done.", 9,
                 "A verb shows an action or a state, such as write, jump or is. An adverb describes a verb and often ends in ly, for example quickly or carefully.\n\n"
                 "In the sentence She walks slowly, walks is the verb and slowly is the adverb.",
                 [Q("In 'He speaks clearly', which word is the adverb?", ["He", "speaks", "clearly", "None"], 2),
                  Q("Which word is a verb?", ["happy", "table", "swim", "green"], 2)]),
            ]),
            ("Tenses and Punctuation", [
                ("Simple Tenses", "Past, present and future in one minute.", 10,
                 "The simple present describes habits and facts: I walk to school. The simple past describes finished actions: I walked yesterday.\n\n"
                 "The simple future uses will: I will walk tomorrow.",
                 [Q("Which sentence is in the past tense?", ["I eat rice", "I ate rice", "I will eat rice", "I am eating rice"], 1)]),
                ("Commas and Full Stops", "Make your writing clear.", 7,
                 "A full stop ends a statement. A comma separates items in a list or joins parts of a sentence, for example: We bought rice, beans, and plantain.\n\n"
                 "A question ends with a question mark.",
                 [Q("What ends a question?", ["A comma", "A full stop", "A question mark", "A colon"], 2)]),
            ]),
        ],
    ),
    dict(
        title="Physics: Motion and Energy",
        description="Speed, acceleration, forces and energy using everyday examples.",
        subject="Science", level="Intermediate", accent="blue",
        curriculum=[
            ("Motion", [
                ("Speed and Velocity", "How fast, and in which direction.", 9,
                 "Speed is the distance travelled divided by the time taken. A car that covers 120 kilometres in 2 hours has a speed of 60 kilometres per hour.\n\n"
                 "Velocity is speed in a given direction, so two cars with the same speed can have different velocities.",
                 [Q("Speed equals...", ["distance x time", "distance / time", "time / distance", "mass x speed"], 1),
                  Q("120 km in 2 hours is...", ["30 km/h", "60 km/h", "120 km/h", "240 km/h"], 1)]),
                ("Acceleration", "How quickly velocity changes.", 9,
                 "Acceleration is the change in velocity divided by the time taken. A bicycle that speeds up from 0 to 6 metres per second in 3 seconds has an acceleration of 2 metres per second squared.",
                 [Q("Acceleration measures a change in...", ["mass", "velocity", "colour", "temperature"], 1)]),
            ]),
            ("Forces and Energy", [
                ("Newton's Second Law", "Force, mass and acceleration.", 10,
                 "Newton's second law says force equals mass multiplied by acceleration. Pushing a heavier object needs more force to give it the same acceleration.\n\n"
                 "A 2 kilogram object accelerating at 3 metres per second squared needs a force of 6 newtons.",
                 [Q("Force equals...", ["mass x acceleration", "mass / acceleration", "speed x time", "weight / time"], 0)]),
                ("Kinetic and Potential Energy", "Energy of motion and of position.", 9,
                 "Kinetic energy is the energy of a moving object. Potential energy is stored energy, for example a ball held high above the ground.\n\n"
                 "Energy is never lost; it changes from one form to another.",
                 [Q("A ball held high has mostly...", ["kinetic energy", "potential energy", "no energy", "sound energy"], 1)]),
            ]),
        ],
    ),
    dict(
        title="Introduction to Chemistry",
        description="Atoms, elements and the periodic table made easy.",
        subject="Science", level="Beginner", accent="emerald",
        curriculum=[
            ("Matter and Atoms", [
                ("States of Matter", "Solid, liquid and gas.", 7,
                 "Matter exists mainly as a solid, a liquid or a gas. Solids keep their shape, liquids take the shape of their container, and gases spread out to fill any space.\n\n"
                 "Heating a solid can melt it into a liquid, and heating a liquid can make it boil into a gas.",
                 [Q("Which state keeps its own shape?", ["Solid", "Liquid", "Gas", "All of them"], 0)]),
                ("Inside the Atom", "Protons, neutrons and electrons.", 9,
                 "An atom has a nucleus containing protons and neutrons. Electrons move around the nucleus in shells.\n\n"
                 "Protons are positive, electrons are negative and neutrons have no charge, so a normal atom is neutral overall.",
                 [Q("Which particle is negatively charged?", ["Proton", "Neutron", "Electron", "Nucleus"], 2),
                  Q("Where are protons found?", ["In the nucleus", "In the shells", "Outside the atom", "Nowhere"], 0)]),
            ]),
            ("Elements", [
                ("The Periodic Table", "How elements are organised.", 8,
                 "The periodic table arranges elements by their number of protons, called the atomic number. Elements in the same column behave in similar ways.\n\n"
                 "Hydrogen has atomic number 1 and helium has atomic number 2.",
                 [Q("The atomic number is the number of...", ["neutrons", "protons", "shells", "molecules"], 1)]),
                ("Acids and Bases", "A first look at pH.", 8,
                 "The pH scale runs from 0 to 14. Below 7 is acidic, 7 is neutral and above 7 is basic. Lemon juice is acidic, pure water is neutral and soap is basic.",
                 [Q("Pure water has a pH of about...", ["1", "7", "10", "14"], 1)]),
            ]),
        ],
    ),
    dict(
        title="Digital Skills and Internet Safety",
        description="Use computers and the internet confidently and safely.",
        subject="Technology", level="Beginner", accent="violet",
        curriculum=[
            ("Getting Comfortable", [
                ("Using a Computer", "Files, folders and shortcuts.", 7,
                 "A file holds your work, such as a document or photo. A folder groups related files together.\n\n"
                 "Useful shortcuts: Control plus C copies, Control plus V pastes and Control plus Z undoes the last action.",
                 [Q("Which shortcut pastes?", ["Ctrl + C", "Ctrl + V", "Ctrl + Z", "Ctrl + P"], 1)]),
                ("Searching the Web", "Find reliable information fast.", 8,
                 "Use specific keywords when you search, and check who published the page. Trusted sources include schools, government sites and well-known news organisations.\n\n"
                 "Compare at least two sources before you believe surprising claims.",
                 [Q("A good habit when researching is to...", ["trust the first result", "compare several sources", "share it immediately", "skip reading"], 1)]),
            ]),
            ("Staying Safe Online", [
                ("Strong Passwords", "Protect your accounts.", 8,
                 "A strong password is long, unique and hard to guess. A good idea is a phrase of several random words with a number.\n\n"
                 "Never reuse the same password on different sites, and never share it, even with friends.",
                 [Q("A strong password is...", ["your name", "123456", "long and unique", "your birthday"], 2),
                  Q("Should you reuse passwords?", ["Yes", "No", "Only at school", "Only on phones"], 1)]),
                ("Spotting Scams", "Phishing and fake offers.", 9,
                 "Scammers send messages that look real and pressure you to act fast, asking for passwords, bank details or money. Check the sender address, do not click unknown links, and when in doubt ask a trusted adult.",
                 [Q("A message urgently asks for your bank PIN. You should...", ["reply quickly", "ignore and report it", "click the link", "forward to friends"], 1)]),
            ]),
        ],
    ),
    dict(
        title="Financial Literacy",
        description="Budgeting, saving and spending wisely, from the first naira.",
        subject="Business", level="Beginner", accent="amber",
        curriculum=[
            ("Managing Money", [
                ("Budgeting Basics", "Plan before you spend.", 8,
                 "A budget compares your income, the money you receive, with your expenses, the money you spend. Needs such as food and transport come before wants such as games.\n\n"
                 "A simple rule is to save at least a small part of everything you receive.",
                 [Q("A budget compares income with...", ["expenses", "friends", "prices only", "taxes only"], 0),
                  Q("Which is a need?", ["Video game", "Food", "Designer shoes", "Cinema ticket"], 1)]),
                ("Saving and Interest", "Make your money grow.", 9,
                 "Saving means keeping money aside for the future. A savings account pays interest, which is extra money added by the bank. If you save 10,000 at 10 percent a year, you earn 1,000 interest in a year.",
                 [Q("10,000 saved at 10% for a year earns...", ["100", "1,000", "10,000", "10"], 1)]),
            ]),
            ("Spending Wisely", [
                ("Needs vs Wants", "Make better choices.", 7,
                 "Before buying, ask: Do I need this? Can I wait? Is there a cheaper option? Waiting a few days often shows whether you really want something.",
                 [Q("A good question before buying is...", ["Is everyone buying it?", "Do I need this?", "Is it shiny?", "Is it famous?"], 1)]),
                ("Avoiding Debt", "Borrow carefully.", 8,
                 "Debt is money you owe. Borrowing is sometimes useful, but you must repay with interest, so only borrow what you can repay and never to buy things you do not need.",
                 [Q("Debt means...", ["money you owe", "money you saved", "a gift", "a salary"], 0)]),
            ]),
        ],
    ),
    dict(
        title="Entrepreneurship Basics",
        description="From idea to first customer: start a small business with confidence.",
        subject="Business", level="Intermediate", accent="amber",
        curriculum=[
            ("Finding an Idea", [
                ("Solving a Problem", "Great businesses start with a real need.", 8,
                 "Look around for problems people complain about, such as long queues or hard-to-find products. A good business idea solves a real problem better, cheaper or faster than what exists.\n\n"
                 "Talk to at least ten possible customers before you build anything.",
                 [Q("A good business idea starts with...", ["a real problem", "a logo", "a big loan", "a famous name"], 0)]),
                ("Know Your Customer", "Who will pay?", 8,
                 "Your target customer is the group of people most likely to buy. Describe their age, needs and budget. The more clearly you know them, the easier it is to price and promote your product.",
                 [Q("Target customers are...", ["everyone", "the people most likely to buy", "your competitors", "your suppliers"], 1)]),
            ]),
            ("Running the Business", [
                ("Pricing and Profit", "Charge enough to grow.", 9,
                 "Profit equals revenue minus costs. If it costs 300 to make an item and you sell it for 500, your profit is 200 per item.\n\n"
                 "Include every cost: materials, transport and your own time.",
                 [Q("Profit equals...", ["revenue - costs", "revenue + costs", "costs - revenue", "price only"], 0),
                  Q("Cost 300, sell 500. Profit?", ["100", "200", "300", "800"], 1)]),
                ("Marketing on a Budget", "Get your first customers.", 8,
                 "Start free: tell friends and family, use WhatsApp status and social media, and ask happy customers for referrals. Good service creates word-of-mouth, the cheapest marketing of all.",
                 [Q("Which marketing is free?", ["TV adverts", "Word of mouth", "Billboards", "Radio jingles"], 1)]),
            ]),
        ],
    ),
]


def ensure_extra_courses(db) -> int:
    """Insert any missing EXTRA courses (matched by title). Returns how many were added."""
    from app.core.security import hash_password
    from app.db.seed import DEMO_PASSWORD, _course  # lazy import: avoids a circular import

    teacher = db.scalar(select(User).where(User.email == "teacher@lighted.dev"))
    if not teacher:
        teacher = User(full_name="Tara Mensah", email="teacher@lighted.dev",
                       hashed_password=hash_password(DEMO_PASSWORD), role="teacher")
        db.add(teacher)
        db.flush()
    existing = set(db.scalars(select(Course.title)))
    added = 0
    for spec in EXTRA:
        if spec["title"] in existing:
            continue
        _course(db, teacher, **spec)
        added += 1
    db.commit()
    return added
