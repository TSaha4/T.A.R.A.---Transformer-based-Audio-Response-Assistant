"""
Script to generate the enhanced intents.json dataset for TARA.
"""

import json
from pathlib import Path

INTENTS_DATA = {
    "intents": [
        {
            "tag": "greeting",
            "patterns": [
                "hi",
                "hello",
                "hey",
                "hey there",
                "hi there",
                "hello there",
                "good morning",
                "good afternoon",
                "good evening",
                "namaste",
                "what's up",
                "whats up",
                "how are you",
                "how are you doing",
                "howdy",
                "yo",
                "hi bot",
                "hello assistant",
                "hey assistant",
                "greetings",
                "hi friend",
                "good day",
                "hello voice bot",
                "hey tara",
                "hello tara",
                "hi tara",
                "good morning tara",
                "good evening tara",
                "hello how are you",
                "hey tara what's up",
                "hey tara how are you",
                "start chat",
                "wake up tara"
            ],
            "responses": [
                "Hello! I am TARA (Transformer-based Audio & Response Assistant). How can I assist you today?",
                "Hi there! I am TARA. Feel free to ask me anything about AI, Deep Learning, science, campus academics, or general questions.",
                "Hey! TARA is ready to help. Feel free to speak using your microphone or type your question below."
            ]
        },
        {
            "tag": "goodbye",
            "patterns": [
                "bye",
                "goodbye",
                "see you",
                "see you later",
                "take care",
                "good night",
                "catch you later",
                "i am leaving",
                "talk later",
                "bye bye",
                "gotta go",
                "got to go",
                "farewell",
                "see ya",
                "until next time",
                "i will go now",
                "that's all",
                "thats all for now",
                "end chat",
                "close conversation",
                "bye tara",
                "goodbye tara",
                "quit",
                "exit"
            ],
            "responses": [
                "Goodbye! Come back anytime whenever you need assistance with AI, academics, or study concepts.",
                "See you later! Have a wonderful and productive day ahead.",
                "Bye! TARA will be right here whenever you need help again."
            ]
        },
        {
            "tag": "thanks",
            "patterns": [
                "thanks",
                "thank you",
                "thank you so much",
                "thanks a lot",
                "many thanks",
                "thanks buddy",
                "thank you assistant",
                "that helped",
                "that was helpful",
                "appreciate it",
                "i appreciate your help",
                "cheers",
                "thanks for the info",
                "thanks for helping",
                "great thanks",
                "ok thanks",
                "thank u",
                "thanks a ton",
                "much obliged",
                "you are helpful",
                "thanks tara",
                "thank you tara"
            ],
            "responses": [
                "You are very welcome! Ask another question whenever you like.",
                "Happy to help! Is there anything else you would like to explore or learn today?",
                "Glad that was useful! TARA is always here to assist."
            ]
        },
        {
            "tag": "bot_name",
            "patterns": [
                "what is your name",
                "whats your name",
                "who are you",
                "who am i talking to",
                "tell me your name",
                "your name please",
                "are you a bot",
                "are you a chatbot",
                "what should i call you",
                "introduce yourself",
                "who is this",
                "identify yourself",
                "do you have a name",
                "what are you called",
                "are you an ai",
                "are you voice assistant",
                "what bot is this",
                "tell me about yourself",
                "your identity",
                "who created you",
                "who made you",
                "what is tara",
                "who is tara",
                "what does tara mean",
                "what does tara stand for"
            ],
            "responses": [
                "I am TARA, which stands for Transformer-based Audio & Response Assistant. I am an intelligent voice and text conversational AI powered by Deep Learning.",
                "You can call me TARA (Transformer-based Audio & Response Assistant)! I process voice and text in real-time using Deep Learning models and neural intent classification.",
                "I am TARA, your intelligent assistant. I combine Speech Recognition with Deep Learning neural networks to understand questions and generate accurate responses."
            ]
        },
        {
            "tag": "capabilities",
            "patterns": [
                "what can you do",
                "what are your features",
                "how do you work",
                "tell me what you can do",
                "what are your capabilities",
                "help me understand what you do",
                "what can i ask you",
                "how can you help me",
                "what is your purpose",
                "list your features",
                "what features do you have",
                "explain how you work",
                "what technologies do you use",
                "what architecture do you use",
                "how do you process voice",
                "how does speech recognition work here"
            ],
            "responses": [
                "I can listen to your voice using Web Speech API, process your query using an LSTM Deep Learning neural network, maintain conversational context, and respond via synthetic speech. You can ask me about AI/ML, science, academic topics, or general knowledge!",
                "TARA provides end-to-end voice and text conversational AI: Speech-to-Text conversion -> Deep Learning intent classification -> Contextual response generation -> Text-to-Speech audio synthesis.",
                "You can speak or type to me! I handle natural language queries on Deep Learning, machine learning, physics, general facts, campus information, and casual conversation."
            ]
        },
        {
            "tag": "help",
            "patterns": [
                "help",
                "help me",
                "i need help",
                "can you help me",
                "how to use this",
                "user guide",
                "how does this app work",
                "instructions",
                "give me support",
                "i have a problem",
                "how do i speak to you",
                "how to use voice",
                "microphone help",
                "assist me",
                "support please"
            ],
            "responses": [
                "To interact with TARA, click the Microphone button to speak or type your question in the text box. I will process your input with Deep Learning and respond with both text and voice!",
                "I am here to assist! Try asking questions like 'What is deep learning?', 'What is backpropagation?', 'Explain black holes', or ask about courses, exams, and study tips.",
                "Need help? Click the mic button for voice input, adjust the voice speed or pitch in the controls, or type any query in the input bar."
            ]
        },
        {
            "tag": "ai_concepts",
            "patterns": [
                "what is machine learning",
                "what is deep learning",
                "explain neural networks",
                "what is a neural network",
                "what is backpropagation",
                "how does backpropagation work",
                "explain backpropagation",
                "what are transformers in ai",
                "what is a transformer model",
                "why is python popular for ai",
                "why python for machine learning",
                "what is artificial intelligence",
                "difference between ai and machine learning",
                "what is natural language processing",
                "what is nlp",
                "explain supervised learning",
                "what is unsupervised learning",
                "what is reinforcement learning",
                "what are the types of machine learning",
                "what are its types",
                "explain convolutional neural networks",
                "what is cnn",
                "what is recurrent neural network",
                "what is rnn",
                "what is lstm",
                "how do lstms work",
                "what is gradient descent",
                "what is an activation function",
                "what is overfitting in machine learning"
            ],
            "responses": [
                "Machine Learning is a subset of AI where algorithms learn patterns from data. The three primary types are Supervised Learning (labeled data), Unsupervised Learning (unlabeled pattern discovery), and Reinforcement Learning (reward-based decision making).",
                "Deep Learning uses multi-layered artificial neural networks inspired by biological neurons. It excels at feature extraction from complex, unstructured data like audio, text, and images.",
                "Backpropagation is the fundamental training algorithm for neural networks. It calculates the gradient of the loss function with respect to each weight using the mathematical chain rule, propagating error backwards to update model parameters via gradient descent.",
                "Python is popular for AI because of its clean readable syntax, extensive scientific ecosystem (TensorFlow, PyTorch, NumPy, Scikit-learn), high performance C-extensions, and massive community support."
            ]
        },
        {
            "tag": "science_knowledge",
            "patterns": [
                "explain black holes simply",
                "what is a black hole",
                "how do black holes work",
                "what is gravity",
                "explain gravity",
                "what is quantum computing",
                "how do quantum computers work",
                "what is quantum superposition",
                "what is general relativity",
                "what is special relativity",
                "speed of light",
                "what is the speed of light",
                "how big is the universe",
                "explain the big bang theory",
                "what is dna",
                "how does photosynthesis work"
            ],
            "responses": [
                "A black hole is a region in spacetime where gravity is so strong that nothing—not even light—can escape. It forms when massive stars collapse under their own gravity at the end of their lifecycle, concentrating mass into an infinitely dense singularity surrounded by an event horizon.",
                "Quantum computing leverages quantum mechanical phenomena—specifically superposition (qubits existing in multiple states simultaneously) and entanglement—to solve certain complex computational problems exponentially faster than classical computers.",
                "Gravity is the curvature of spacetime caused by mass and energy, as described by Einstein's General Theory of Relativity. Mass tells spacetime how to curve, and curved spacetime tells mass how to move."
            ]
        },
        {
            "tag": "humor",
            "patterns": [
                "tell me a joke",
                "say something funny",
                "make me laugh",
                "crack a joke",
                "do you know any jokes",
                "tell me another joke",
                "tell a funny joke",
                "entertain me",
                "can you tell jokes",
                "give me a joke"
            ],
            "responses": [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "Why did the neural network go to school? To improve its gradient descent and avoid getting stuck in local minima!",
                "An SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'"
            ]
        },
        {
            "tag": "study_help",
            "patterns": [
                "how to study effectively",
                "study tips",
                "how can i improve my grades",
                "how to prepare for exams",
                "study techniques",
                "pomodoro technique",
                "how to avoid distractions while studying",
                "how to prepare for technical interviews",
                "how to learn deep learning",
                "roadmap for machine learning",
                "time management tips for students"
            ],
            "responses": [
                "Effective study strategies include: 1) Active recall and spaced repetition (testing yourself at increasing intervals), 2) The Pomodoro Technique (25 minutes focused study, 5 minutes rest), and 3) The Feynman Technique (teaching the concept in simple terms).",
                "To master Deep Learning: Start with linear algebra and calculus, learn Python & NumPy, build classic ML models with Scikit-learn, and then advance to TensorFlow/Keras for CNNs, RNNs/LSTMs, and Transformers.",
                "For technical interview prep: Practice data structures & algorithms on LeetCode, understand system design fundamentals, and be prepared to explain your Deep Learning project architectures clearly."
            ]
        },
        {
            "tag": "motivation",
            "patterns": [
                "motivate me",
                "give me motivation",
                "i feel stressed",
                "i am feeling anxious",
                "inspire me",
                "give me an inspirational quote",
                "i am tired of studying",
                "i feel overwhelmed",
                "encourage me",
                "words of encouragement",
                "cheer me up",
                "positive quote"
            ],
            "responses": [
                "'The expert in anything was once a beginner.' Take a deep breath, break your challenges into small achievable steps, and keep moving forward!",
                "Consistent small efforts compound into extraordinary achievements. Focus on today's progress, not perfection.",
                "Remember why you started. Every challenging bug you solve and every concept you master is building your future expertise!"
            ]
        },
        {
            "tag": "college",
            "patterns": [
                "about the college",
                "tell me about the college",
                "university information",
                "tell me about the university",
                "campus overview",
                "where is the campus located",
                "campus address",
                "college history",
                "is this a good college",
                "college ranking",
                "accreditation of college"
            ],
            "responses": [
                "Our institution is a premier technological university renowned for excellence in engineering, computer science, and AI research, featuring state-of-the-art research laboratories and world-class faculty.",
                "The university campus offers world-class academic infrastructure, high-performance computing labs, extensive sports complexes, and vibrant innovation incubators."
            ]
        },
        {
            "tag": "courses",
            "patterns": [
                "what courses are offered",
                "tell me about courses",
                "btech branches",
                "mtech specializations",
                "computer science course",
                "ai and ml branch",
                "syllabus for computer science",
                "course curriculum",
                "academic programs",
                "undergraduate programs",
                "postgraduate programs",
                "degree options"
            ],
            "responses": [
                "We offer B.Tech, M.Tech, and Ph.D. programs across Computer Science, Artificial Intelligence & Machine Learning, Data Science, Electronics, and Mechanical Engineering.",
                "The curriculum includes foundational computer science, Deep Learning, Natural Language Processing, Cloud Computing, and hands-on capstone industry projects."
            ]
        },
        {
            "tag": "exams",
            "patterns": [
                "when are the exams",
                "exam schedule",
                "semester exam dates",
                "mid term exams",
                "continuous assessment tests",
                "cat exam dates",
                "fat exam dates",
                "final assessment test",
                "how are exams conducted",
                "grading system",
                "gpa calculation",
                "revaluation process"
            ],
            "responses": [
                "The semester evaluation includes Continuous Assessment Tests (CAT 1 & CAT 2), lab assessments, and the comprehensive Final Assessment Test (FAT). Please verify exact schedules on the student portal.",
                "Grading follows a relative/absolute grading scale based on overall credit points. Hall tickets are accessible on the student portal 10 days before exams."
            ]
        },
        {
            "tag": "attendance",
            "patterns": [
                "what is the attendance policy",
                "minimum attendance required",
                "is 75 percent attendance mandatory",
                "what happens if attendance is low",
                "attendance rules",
                "how to check my attendance",
                "medical leave for attendance",
                "on duty attendance policy",
                "debar criteria"
            ],
            "responses": [
                "A minimum of 75% attendance is mandatory in each course to be eligible for the Final Assessment Test (FAT). Medical leave and On-Duty (OD) certificates must be submitted within 3 working days.",
                "You can monitor your real-time attendance through the student portal dashboard under the Academic Attendance module."
            ]
        },
        {
            "tag": "timetable",
            "patterns": [
                "class timetable",
                "where can i see my schedule",
                "class schedule",
                "lecture timings",
                "when do classes start",
                "daily schedule",
                "slot timetable",
                "how are class slots allocated"
            ],
            "responses": [
                "Classes generally run from 8:00 AM to 6:30 PM across designated morning and afternoon theory and lab slots. Your customized timetable is visible on the student portal.",
                "Your registered course slots, room allocations, and faculty details are available on your student portal profile."
            ]
        },
        {
            "tag": "fees",
            "patterns": [
                "what is the fee structure",
                "tuition fees",
                "hostel fees",
                "how to pay fees",
                "online fee payment",
                "fee payment deadline",
                "is there a scholarship",
                "scholarship criteria",
                "late fee penalty",
                "fee refund policy"
            ],
            "responses": [
                "Tuition and hostel fees can be paid securely online via net banking, UPI, or debit/credit cards through the student finance portal.",
                "Merit-based and sports scholarships are available for eligible students. For fee breakdowns and payment receipts, check the student finance portal."
            ]
        },
        {
            "tag": "placements",
            "patterns": [
                "how are the placements",
                "campus placement statistics",
                "top recruiters",
                "average package",
                "highest package",
                "placement training",
                "companies visiting campus",
                "career development cell"
            ],
            "responses": [
                "Our campus maintains an outstanding placement record with over 800+ visiting companies including top tech giants, offering competitive compensation packages.",
                "The Career Development Centre (CDC) organizes regular mock interviews, competitive coding bootcamps, and soft skill workshops to prepare students."
            ]
        },
        {
            "tag": "internships",
            "patterns": [
                "internship opportunities",
                "how to get an internship",
                "summer internships",
                "industrial training",
                "can i do a semester internship",
                "internship credits",
                "research internships"
            ],
            "responses": [
                "Students can undertake summer internships or final semester capstone industrial projects. Internship credits can be mapped to academic credits upon department approval.",
                "The Placement & Internship office regularly circulates verified opportunities from leading industrial and research organizations."
            ]
        },
        {
            "tag": "library",
            "patterns": [
                "library timings",
                "is the library open on weekends",
                "how to borrow books",
                "digital library access",
                "ieee journal access",
                "central library facilities",
                "how many books can i issue"
            ],
            "responses": [
                "The Central Library is open daily from 8:00 AM to 10:00 PM, with 24/7 access during exam periods. It provides access to millions of physical volumes and digital repositories (IEEE, ACM, Springer).",
                "Students can issue up to 6 books simultaneously using their Student ID Smart Card for a duration of 14 days."
            ]
        },
        {
            "tag": "hostel",
            "patterns": [
                "hostel facilities",
                "hostel room allotment",
                "is hostel mandatory",
                "hostel mess food",
                "hostel curfew timings",
                "hostel wifi",
                "ac hostel rooms",
                "laundry facility in hostel"
            ],
            "responses": [
                "Campus hostels offer AC and Non-AC rooms (single to multi-bed options), high-speed Wi-Fi, 24/7 security, gymnasium facilities, and multi-cuisine mess catering.",
                "Hostel curfew is strictly observed for student safety. Outing requests and night leaves must be submitted through the parent-approved online hostel portal."
            ]
        },
        {
            "tag": "events",
            "patterns": [
                "upcoming events",
                "college fests",
                "technical symposium",
                "cultural fest",
                "hackathons on campus",
                "student clubs and chapters",
                "sports tournaments"
            ],
            "responses": [
                "The university hosts annual international techno-management fests, cultural extravaganzas, and 24-hour hackathons, along with year-round workshops across 50+ student chapters.",
                "Event registrations and schedules are posted on the university events portal and student club noticeboards."
            ]
        },
        {
            "tag": "contact",
            "patterns": [
                "contact details",
                "helpdesk phone number",
                "admission office email",
                "how to reach administration",
                "campus emergency contact",
                "faculty contact info"
            ],
            "responses": [
                "You can reach the central university helpdesk at helpdesk@university.edu or call the administration office during working hours.",
                "For urgent medical or campus security assistance, the 24/7 Emergency Control Room is reachable directly via the campus helpline."
            ]
        },
        {
            "tag": "working_hours",
            "patterns": [
                "working hours",
                "office timings",
                "administrative office hours",
                "is the office open today",
                "weekend working hours",
                "when does the office close"
            ],
            "responses": [
                "Administrative and academic department offices operate Monday through Friday from 9:00 AM to 5:00 PM, and on designated working Saturdays.",
                "Emergency services, healthcare centres, and security desks operate 24 hours a day, 7 days a week."
            ]
        },
        {
            "tag": "fallback",
            "patterns": [
                "asdfghjkl",
                "xyzabc",
                "gibberish input",
                "random letters",
                "qwertyuiop",
                "unintelligible sounds",
                "blablabla",
                "1234567890",
                "zzzzz"
            ],
            "responses": [
                "I didn't quite catch that. Could you please rephrase your question or ask about AI, Deep Learning, science, or academics?",
                "I want to make sure I understand correctly. Please try typing or speaking your question again in clear terms.",
                "TARA couldn't find a direct match for that phrase. Feel free to ask about machine learning, physics, campus info, or study tips!"
            ]
        }
    ]
}

if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent / "intents.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(INTENTS_DATA, f, indent=2, ensure_ascii=False)
    print(f"Successfully generated {out_file} with {len(INTENTS_DATA['intents'])} intents.")
