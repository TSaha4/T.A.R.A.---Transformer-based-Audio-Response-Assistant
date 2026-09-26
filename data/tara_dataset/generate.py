#!/usr/bin/env python3
"""
TARA synthetic chatbot dataset generator.
Produces: intent, utterance, response, entities (JSON) across 19 intents.
Fully synthetic, template + slot-filling based (no copied/scraped data).
"""
import json, csv, random, itertools, hashlib
from collections import defaultdict

random.seed(42)

TARGET_MIN = 550
TARGET_MAX = 750

# ----------------------------------------------------------------------
# Shared slot vocabularies
# ----------------------------------------------------------------------
NAMES_FOR_TARA = ["Tara", "TARA", "tara", "Tara AI"]
POLITE_PREFIX = ["", "please ", "could you ", "can you ", "would you ",
                  "hey, ", "so, ", "um, ", "quick one - ", "just wondering, ",
                  "real quick, "]
POLITE_SUFFIX = ["", " please", " thanks", " if you can", " right now",
                  "?", " tara", " tara?"]
CASUAL_TAGS = ["", " man", " dude", " buddy", " friend", " ya"]

CITIES = ["Chennai", "Mumbai", "Delhi", "Bangalore", "Vellore", "Hyderabad",
          "Kolkata", "Pune", "Jaipur", "Ranchi", "Kochi", "Lucknow",
          "New York", "London", "Tokyo", "Paris", "Singapore", "Dubai",
          "Toronto", "Sydney", "Berlin", "Amsterdam", "San Francisco",
          "Chicago", "Coimbatore", "Nagpur", "Bhopal", "Patna", "Goa", "Surat"]

DAYS = ["today", "tomorrow", "tonight", "this evening", "this weekend",
        "on Monday", "on Tuesday", "on Wednesday", "on Thursday", "on Friday",
        "on Saturday", "on Sunday", "next week", "this afternoon", "this morning"]

CLOCK_TIMES = ["5 pm", "6:30 am", "noon", "midnight", "9 am", "10:15 pm",
               "7 o'clock", "half past three", "quarter to nine", "11 am",
               "2:45 pm", "8 pm", "6 am", "1 pm", "4:30 pm"]

TASKS = ["submit the assignment", "call mom", "pay the electricity bill",
         "buy groceries", "finish the lab report", "revise DBMS notes",
         "attend the club meeting", "book the train ticket", "water the plants",
         "send the email to my professor", "pack for the trip", "walk the dog",
         "review the pull request", "prepare slides for the presentation",
         "renew my gym membership", "pick up the laundry", "read chapter 5",
         "backup my laptop", "schedule the dentist appointment",
         "submit the internship application", "practice for the interview",
         "clean my room", "update my resume", "pay the hostel fee",
         "return the library books", "charge my phone", "check the exam timetable",
         "reply to the recruiter", "fix the bug in my project", "test the API endpoint"]

STUDY_SUBJECTS = ["data structures", "operating systems", "machine learning",
                   "deep learning", "computer networks", "DBMS", "algorithms",
                   "linear algebra", "probability and statistics",
                   "natural language processing", "computer architecture",
                   "object-oriented programming", "compiler design",
                   "software engineering", "graph theory", "calculus",
                   "discrete mathematics", "system design", "Java",
                   "Python", "SQL", "TCP/IP", "neural networks", "GATE CS"]

KNOWLEDGE_TOPICS = ["black holes", "photosynthesis", "blockchain", "quantum computing",
                     "the French Revolution", "climate change", "machine learning",
                     "the water cycle", "artificial intelligence", "neural networks",
                     "the stock market", "DNA replication", "the solar system",
                     "cryptography", "evolution", "the internet", "gravity",
                     "the human brain", "renewable energy", "supply and demand",
                     "inflation", "vaccines", "the immune system", "plate tectonics",
                     "nuclear energy", "electric vehicles", "the periodic table",
                     "GDP", "interest rates", "space exploration"]

GENERAL_FACT_QS = [
    ("What is the capital of France?", "Paris is the capital of France."),
    ("What is the capital of Japan?", "Tokyo is the capital of Japan."),
    ("What is the capital of India?", "New Delhi is the capital of India."),
    ("Who wrote Romeo and Juliet?", "William Shakespeare wrote Romeo and Juliet."),
    ("How many continents are there?", "There are seven continents on Earth."),
    ("What is the largest planet in the solar system?", "Jupiter is the largest planet in our solar system."),
    ("What is the boiling point of water?", "Water boils at 100 degrees Celsius at sea level."),
    ("How many days are there in a leap year?", "A leap year has 366 days."),
    ("What is the speed of light?", "The speed of light is about 299,792 kilometers per second."),
    ("Who painted the Mona Lisa?", "Leonardo da Vinci painted the Mona Lisa."),
    ("What is the tallest mountain in the world?", "Mount Everest is the tallest mountain above sea level."),
    ("What is the chemical symbol for gold?", "The chemical symbol for gold is Au."),
    ("How many players are on a football team?", "A standard football (soccer) team has 11 players on the field."),
    ("What is the currency of Japan?", "The currency of Japan is the yen."),
    ("Who is known as the father of computers?", "Charles Babbage is often called the father of computers."),
    ("What is the smallest prime number?", "The smallest prime number is 2."),
    ("How many bones are in the human body?", "An adult human body has 206 bones."),
    ("What is the longest river in the world?", "The Nile is generally considered the longest river in the world."),
    ("What year did India gain independence?", "India gained independence in 1947."),
    ("What is the freezing point of water in Fahrenheit?", "Water freezes at 32 degrees Fahrenheit."),
]

MOODS_NEG = ["sad", "stressed", "anxious", "tired", "overwhelmed", "frustrated",
             "exhausted", "down", "burnt out", "nervous", "lonely", "low",
             "irritated", "drained", "hopeless", "discouraged"]
MOODS_POS = ["happy", "great", "excited", "good", "relaxed", "fantastic",
             "energetic", "motivated", "cheerful", "awesome", "pretty good", "on top of the world",
             "confident", "proud", "grateful", "inspired"]
MOODS_NEU = ["okay", "fine", "meh", "alright", "so-so", "not sure how I feel"]

JOKE_TOPICS = ["", " about programmers", " about AI", " about cats", " about exams",
               " about Mondays", " about coffee", " about robots", " about college life",
               " about engineers"]

PREFIX_POOL_CASUAL = ["", "hey tara, ", "hey, ", "um, ", "so, ", "okay so, ",
                       "listen, ", "well, ", "honestly, ", "just so you know, ",
                       "quick thing, ", "by the way, "]
SUFFIX_POOL_STATEMENT = ["", ".", "!", " tara", " tara.", " for now", " ok"]
SUFFIX_POOL_QUESTION = ["", "?", " tara", " tara?", " right now", " right now?"]

GIBBERISH = ["asdkjfh", "qwerty12345", "blah blah blah", "xzy qq mmm",
             "purple elephants fly upward", "does the color seven taste loud",
             "flarn gibbet zonk", "12 34 56 78 90 !!!", "..........",
             "???!!!???", "wibble wobble tim", "the the the the", "kjshdfkjshdf",
             "banana banana banana phone", "zzzzzzzzzzzzz", "asdf;lkj asdf;lkj",
             "moo cluck oink quack", "??????????", "help help help help help",
             "1 + 1 = fish", "green idea sleeps furiously", "qazwsx edcrfv",
             "lorem ipsum dolor blah", "snorlax quibble frog", "asdfghjkl",
             "mmmmmm nnnnnn oooooo", "the sky is made of noodles today",
             "gorble morble snorp", "12345 abcde zzzzz", "flibbertigibbet nonsense text",
             "purple monday tuesday soup", "kablooey splat wonk", "zibber zabber",
             "xkcd xkcd xkcd", "does purple sound like tuesday", "wooooooosh bam pow",
             "quixotic flumberjack noodle", "the moon owes me five dollars",
             "spork spork spork spork", "hjkl hjkl hjkl", "vwxyz vwxyz",
             "grumpy toaster explains taxes", "the number seven is jealous",
             "asdf1234 qwer5678", "mnbvcxz mnbvcxz", "flibber jabber wobber",
             "yodel filibuster carousel", "the printer dreams in binary",
             "zap zonk fizzle pop", "squiggly wiggly jiggly"]

OUT_OF_SCOPE_EXTRA = [
    "can you file my taxes for me", "diagnose why my car won't start",
    "write code that hacks a bank", "can you fly a drone for me right now",
    "tell me next week's winning lottery numbers", "can you perform surgery instructions",
    "unlock someone else's phone for me", "can you control my thermostat",
    "place a food delivery order right now", "predict the exact stock price tomorrow",
    "can you drive my car", "read my mind", "can you see through my camera",
    "delete all the files on my computer", "can you pay my rent",
    "what am i thinking right now", "can you feel emotions like humans do",
    "give me someone else's personal information", "can you make me invisible",
    "solve world hunger right now", "can you time travel",
    "predict the next earthquake exactly", "can you print money for me",
    "give me the answers to tomorrow's exam", "can you fix my broken phone screen",
    "teleport me to paris", "can you sign legal documents for me",
]

# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------
def cap(s):
    return s[0].upper() + s[1:] if s else s

def dedupe_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        k = x.strip().lower()
        if k not in seen and x.strip():
            seen.add(k)
            out.append(x.strip())
    return out

def sample_to_range(items, lo=TARGET_MIN, hi=TARGET_MAX):
    items = dedupe_keep_order(items)
    random.shuffle(items)
    if len(items) > hi:
        items = items[:hi]
    return items

def expand_phrases(base_list, prefixes, suffixes, extra_list=None, target=TARGET_MAX):
    """Combinatorially wrap base phrases with prefixes/suffixes to build a
    large pool of paraphrase-like variants, then dedupe and cap at target."""
    combos = []
    for b in base_list:
        for p in prefixes:
            for s in suffixes:
                combos.append(f"{p}{b}{s}".strip())
    if extra_list:
        combos.extend(extra_list)
    combos = dedupe_keep_order(combos)
    random.shuffle(combos)
    if len(combos) > target:
        combos = combos[:target]
    return combos

# ----------------------------------------------------------------------
# Each generator returns list of (utterance, response, entities_dict)
# ----------------------------------------------------------------------
DATA = defaultdict(list)

# ---------------- GREETING ----------------
def gen_greeting():
    base_greets = ["hi", "hello", "hey", "yo", "hiya", "heya", "sup", "howdy",
                   "good morning", "good afternoon", "good evening", "morning",
                   "evening", "greetings", "hey there", "hi there", "hello there",
                   "what's up", "hi tara", "hello tara", "hey tara", "yo tara",
                   "hiya tara", "good morning tara", "good evening tara",
                   "namaste", "namaste tara", "hola", "hola tara"]
    responses = [
        "Hey! How can I help you today?",
        "Hello there! What can I do for you?",
        "Hi! I'm TARA, ready when you are.",
        "Hey! Good to see you. What's on your mind?",
        "Hello! How can I assist you right now?",
        "Hi there! Let me know what you need.",
        "Hey, welcome back! What are we working on today?",
    ]
    out = []
    for g in base_greets:
        for pre in ["", "well ", "oh "]:
            for suf in ["", "!", ".", " :)", ", how are you", ", tara"]:
                u = f"{pre}{g}{suf}".strip()
                out.append((cap(u), random.choice(responses), {}))
    # extra natural variants
    extra = ["hey tara are you there", "hi is anyone there", "hello can you hear me",
             "hey tara you up", "morning tara", "evening tara, how's it going",
             "hi tara it's me again", "hey it's been a while", "yo what's good",
             "hello hello", "hiya, long time no chat", "hey, first time using this"]
    for u in extra:
        out.append((cap(u), random.choice(responses), {}))
    return out

# ---------------- GOODBYE ----------------
def gen_goodbye():
    base = ["bye", "goodbye", "see you", "see you later", "see ya", "catch you later",
            "talk to you later", "gotta go", "i'm off", "i'm leaving now", "ttyl",
            "bye tara", "goodbye tara", "see you tara", "later", "peace out",
            "signing off", "good night", "goodnight", "good night tara",
            "take care", "i have to go now", "logging off", "i'll talk to you later",
            "farewell", "farewell tara", "cya", "cya later", "im done for now",
            "that's all for now", "im heading out"]
    responses = [
        "Goodbye! Talk soon.",
        "See you later! Take care.",
        "Bye! I'll be here whenever you need me.",
        "Catch you later! Have a great day.",
        "Take care! Come back anytime.",
        "Goodnight! Sleep well.",
        "Alright, signing off. Talk soon!",
    ]
    extra = ["okay bye then", "alright im done, bye", "thanks bye", "cool see you tomorrow",
             "gotta run, bye tara", "im logging off now, night", "see you next time",
             "okay that's it for today", "im gonna go now", "talk later, take it easy"]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_STATEMENT, extra_list=extra)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- THANKS ----------------
def gen_thanks():
    base = ["thanks", "thank you", "thanks a lot", "thank you so much", "thanks tara",
            "thank you tara", "appreciate it", "i appreciate it", "much appreciated",
            "thanks so much", "ty", "thx", "thankyou", "great, thanks", "perfect, thank you",
            "awesome thanks", "cool thanks", "thanks for the help", "thank you for helping",
            "thanks a ton", "many thanks", "thanks for that", "thanks tara, that helped",
            "you're a lifesaver", "that was really helpful, thanks", "thanks a million",
            "appreciate the help", "thanks for the quick reply", "thank you kindly",
            "cheers for that"]
    responses = [
        "You're welcome! Happy to help.",
        "Anytime! Let me know if you need anything else.",
        "No problem at all!",
        "Glad I could help!",
        "You're welcome! That's what I'm here for.",
        "Of course! Reach out anytime.",
    ]
    extra = ["thanks that really helped me out", "thank you, saved me a lot of time",
             "cool, appreciate the quick help", "thanks tara you're the best",
             "thank you for explaining that", "thanks for sorting that out",
             "thanks for reminding me", "appreciate you being patient with me"]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_STATEMENT, extra_list=extra)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- HELP ----------------
def gen_help():
    base = ["help", "help me", "i need help", "can you help me", "i need assistance",
            "what can you do", "how do i use you", "how does this work",
            "show me what you can do", "list your commands", "what are your features",
            "i'm stuck", "i don't know what to do", "can you assist me",
            "help me out", "what commands do you support", "how do i get started",
            "guide me", "i need some guidance", "what should i say to you",
            "how can you help me", "explain how to use tara", "what are you capable of",
            "give me a list of things you can help with", "i'm confused, help",
            "can you walk me through your features", "how do i talk to you",
            "what kind of things can i ask you", "need some help here",
            "tara i need help with something"]
    responses = [
        "I can chat with you, set reminders, manage tasks, answer general questions, help you study, tell jokes, and more. Just tell me what you need!",
        "Sure! I can help with reminders, tasks, quick facts, study support, small talk, and more. What would you like to do?",
        "I'm here to help with things like setting reminders, answering questions, tracking tasks, and casual conversation. What do you need?",
        "Happy to help. You can ask me about the time, date, weather, set reminders, get study help, or just chat.",
    ]
    extra = ["i don't understand how to use this app", "what am i supposed to ask you",
             "can you give me some examples of what to say", "sos i need help",
             "yo i need a hand with something", "how do reminders work in this app",
             "not sure what you can do, explain please", "give me a quick tutorial"]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_QUESTION, extra_list=extra)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- ABOUT_TARA ----------------
def gen_about():
    base = ["who are you", "what are you", "tell me about yourself", "what is tara",
            "who is tara", "are you a robot", "are you human", "are you an ai",
            "what's your name", "do you have a name", "who made you",
            "who created you", "are you a chatbot", "what is your purpose",
            "tell me about tara", "describe yourself", "are you a real person",
            "what kind of assistant are you", "are you google assistant",
            "are you siri", "are you alexa", "are you chatgpt", "what technology do you use",
            "are you a transformer model", "how were you built", "what makes you different",
            "are you always listening", "can i trust you with my data",
            "what's the meaning of your name", "why are you called tara"]
    responses = [
        "I'm TARA — Transformer-based Audio & Response Assistant. I'm an AI voice-enabled chatbot built to help with everyday tasks, reminders, study support, and conversation.",
        "I'm TARA, an AI assistant. I use deep learning to understand what you say and respond helpfully — think of me as a friendly voice-enabled helper.",
        "I'm an AI, not a human. My name is TARA, and I'm designed to chat, manage reminders and tasks, and answer your questions.",
        "TARA stands for Transformer-based Audio & Response Assistant. I was built as a voice-enabled deep learning chatbot to make everyday tasks easier.",
    ]
    extra = ["so what exactly is tara", "explain what kind of assistant you are",
             "i'm curious what you're built with", "are you like siri or alexa",
             "do you run on a neural network", "what's the tech behind you",
             "give me a quick intro about yourself", "are you open source"]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_QUESTION, extra_list=extra)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- SMALL_TALK ----------------
def gen_small_talk():
    base = ["how are you", "how's it going", "how are you doing", "what's up",
            "how's your day", "how have you been", "what's new", "how's life",
            "are you okay", "how do you feel", "what are you up to",
            "having a good day", "is everything alright with you",
            "how's your day going so far", "what have you been doing",
            "tell me something interesting", "let's chat", "talk to me",
            "i'm bored, entertain me", "say something fun", "make conversation",
            "what do you think about life", "do you dream", "do you get tired",
            "do you sleep", "do you ever get bored", "what's your favorite color",
            "do you have feelings", "can we just talk for a bit", "keep me company"]
    responses = [
        "I'm doing great, thanks for asking! How about you?",
        "All good on my end! What's going on with you?",
        "I'm just here, ready to chat whenever you are.",
        "Doing well! Anything fun happening in your day?",
        "I don't have feelings the way you do, but I enjoy our chats! How are you?",
        "Pretty good! What's on your mind today?",
    ]
    extra = ["hey just checking in, how are things", "so how's your day been so far",
             "wanna have a casual chat", "im just here killing time, talk to me",
             "you doing alright over there", "any interesting updates today"]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_QUESTION, extra_list=extra)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- TIME ----------------
def gen_time():
    base = ["what time is it", "tell me the time", "current time please",
            "do you know the time", "what's the time right now", "give me the time",
            "can you tell me the time", "time check", "what time do you have",
            "what's the current time", "time please", "may i know the time",
            "could you tell me what time it is", "i need to know the time",
            "what time is it now", "time right now"]
    responses_tpl = [
        "I can't check a live clock from here, but your device should show the current time.",
        "I don't have access to real-time clock data right now, but you can check your phone or system clock.",
        "I'm not connected to a live time source at the moment — your device's clock will have the exact time.",
    ]
    out = []
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_QUESTION, target=500)
    for u in pool:
        out.append((cap(u), random.choice(responses_tpl), {}))
    for c in CITIES[:18]:
        u = f"what time is it in {c}"
        out.append((cap(u), f"I can't fetch live time zones right now, but I can help if you tell me {c}'s UTC offset.", {"city": c}))
        u2 = f"what's the current time in {c} right now"
        out.append((cap(u2), f"I don't have a live feed for {c}'s time zone at the moment.", {"city": c}))
    extra = ["hey what time is it over there", "quick, what time is it",
             "is it late right now", "what time is it where you are"]
    for u in extra:
        out.append((cap(u), random.choice(responses_tpl), {}))
    return out

# ---------------- DATE ----------------
def gen_date():
    base = ["what's the date today", "what date is it", "tell me today's date",
            "what's today's date", "can you tell me the date", "date check",
            "what day is it today", "what's the day today", "what day of the week is it",
            "which day is it", "give me today's date", "do you know the date today",
            "what's the date", "could you tell me what day it is",
            "what's today's day and date", "current date please"]
    responses_tpl = [
        "I don't have access to a live calendar right now, but your device should show today's date.",
        "I can't check the live date from here — take a look at your phone or system calendar.",
        "I'm not connected to a real-time calendar at the moment.",
    ]
    extra_base = ["what's the date going to be tomorrow", "remind me what today's date is",
             "hey what day is it, i lost track", "is today a weekday or weekend",
             "what's the date this coming friday", "what's the date next monday",
             "how many days until friday", "is today a public holiday",
             "what's the date three days from now", "what day was it yesterday"]
    pool = expand_phrases(base + extra_base, PREFIX_POOL_CASUAL, SUFFIX_POOL_QUESTION, target=650)
    return [(cap(u), random.choice(responses_tpl), {}) for u in pool]

# ---------------- WEATHER ----------------
def gen_weather():
    templates = [
        "what's the weather like in {c}",
        "how's the weather in {c}",
        "is it raining in {c}",
        "weather forecast for {c}",
        "will it rain {d} in {c}",
        "what's the temperature in {c}",
        "is it sunny in {c} today",
        "should i carry an umbrella in {c}",
        "what's the weather {d}",
        "give me the weather update for {c}",
        "is it cold in {c} right now",
        "how hot is it in {c} today",
        "weather in {c} {d}",
        "will it be windy in {c}",
        "check the weather for {c}",
        "is it going to snow in {c}",
        "how's the weather looking in {c} {d}",
        "do i need a jacket in {c}",
        "is it humid in {c} right now",
        "what's the forecast like in {c} {d}",
        "any chance of thunderstorms in {c}",
        "how warm is it in {c}",
    ]
    responses_tpl = [
        "I don't have live weather data right now, but I'd recommend checking a weather app for {c}.",
        "I can't pull real-time weather for {c} at the moment — a weather app will have the latest forecast.",
        "I'm not connected to a live weather feed, so I can't confirm conditions in {c} right now.",
    ]
    out = []
    for t in templates:
        for c in CITIES:
            d = random.choice(DAYS)
            u = t.format(c=c, d=d)
            ents = {"city": c}
            if "{d}" in t:
                ents["date"] = d
            out.append((cap(u), random.choice(responses_tpl).format(c=c), ents))
    return out

# ---------------- REMINDER ----------------
def gen_reminder():
    templates = [
        "remind me to {task} at {time}",
        "remind me to {task} {day}",
        "set a reminder to {task} at {time} {day}",
        "can you remind me to {task}",
        "please remind me to {task} {day}",
        "i need a reminder to {task} at {time}",
        "set a reminder for {task}",
        "don't let me forget to {task}",
        "remind me at {time} to {task}",
        "create a reminder to {task} on {day}",
        "ping me at {time} to {task}",
        "add a reminder: {task} at {time}",
        "remind me {day} to {task}",
        "could you set a reminder to {task} at {time}",
        "notify me to {task} {day}",
    ]
    responses_tpl = [
        "Got it! I'll remind you to {task} at {time}.",
        "Reminder set — I'll nudge you to {task} {day}.",
        "Sure, I've noted a reminder to {task}.",
        "Okay, I'll remind you to {task} {day} at {time}.",
    ]
    out = []
    for t in templates:
        for _ in range(60):
            task = random.choice(TASKS)
            time_ = random.choice(CLOCK_TIMES)
            day = random.choice(DAYS)
            u = t.format(task=task, time=time_, day=day)
            ents = {"task": task}
            if "{time}" in t:
                ents["time"] = time_
            if "{day}" in t:
                ents["date"] = day
            resp = random.choice(responses_tpl).format(task=task, time=time_, day=day)
            out.append((cap(u), resp, ents))
    return out

# ---------------- TASK ----------------
def gen_task():
    add_templates = [
        "add a task to {task}",
        "add {task} to my task list",
        "create a task: {task}",
        "i need to {task}, add it to my list",
        "new task: {task}",
        "put {task} on my to-do list",
        "add task {task}",
    ]
    done_templates = [
        "mark {task} as done",
        "i finished {task}", "i completed {task}",
        "mark the task {task} as complete",
        "check off {task}",
        "{task} is done now",
    ]
    list_templates = [
        "show me my tasks", "what are my pending tasks", "list my tasks",
        "what's on my to-do list", "show my task list", "what tasks do i have today",
        "give me my pending to-dos", "what's left on my list", "show incomplete tasks",
        "what do i still need to do", "display all my tasks", "any tasks due today",
        "what tasks are pending", "show me what's on my plate today",
    ]
    delete_templates = [
        "delete the task {task}", "remove {task} from my list",
        "cancel the task {task}", "get rid of the {task} task",
    ]
    responses_add = ["Added '{task}' to your task list.", "Got it, '{task}' is now on your list.",
                      "Task added: {task}."]
    responses_done = ["Nice work! I've marked '{task}' as done.", "Great, '{task}' is now complete.",
                       "Marked '{task}' as finished. Good job!"]
    responses_list = ["Here are your pending tasks: (this is a demo, so I don't have live task storage yet).",
                       "You currently have a few tasks pending — check your task list for details.",
                       "Let me pull up your to-do list for you."]
    responses_del = ["Removed '{task}' from your list.", "Okay, '{task}' has been deleted.",
                      "Done — '{task}' is no longer on your list."]
    out = []
    for t in add_templates:
        for task in TASKS:
            u = t.format(task=task)
            out.append((cap(u), random.choice(responses_add).format(task=task), {"task": task, "action": "add"}))
    for t in done_templates:
        for task in TASKS:
            u = t.format(task=task)
            out.append((cap(u), random.choice(responses_done).format(task=task), {"task": task, "action": "complete"}))
    list_pool = expand_phrases(list_templates, PREFIX_POOL_CASUAL, SUFFIX_POOL_QUESTION, target=250)
    for u in list_pool:
        out.append((cap(u), random.choice(responses_list), {"action": "list"}))
    for t in delete_templates:
        for task in TASKS:
            u = t.format(task=task)
            out.append((cap(u), random.choice(responses_del).format(task=task), {"task": task, "action": "delete"}))
    return out

# ---------------- GENERAL_QUERY ----------------
def gen_general_query():
    out = []
    prefixes = ["", "hey tara, ", "quick question - ", "i was wondering, ", "so, ",
                "random question, ", "just curious, ", "do you happen to know, ",
                "off the top of your head, ", "quick fact check, ",
                "trivia time, ", "here's one for you, ", "pop quiz, ",
                "can i ask, ", "tell me, "]
    for q, a in GENERAL_FACT_QS:
        for pre in prefixes:
            u = f"{pre}{q[0].lower()}{q[1:]}" if pre else q
            out.append((cap(u), a, {}))
        for suf in ["do you know", "can you tell me", "any idea", "would you happen to know",
                    "i forget", "remind me"]:
            u = f"{suf}, {q[0].lower()}{q[1:]}"
            out.append((cap(u), a, {}))
    generic_templates = [
        "how many {x} are there in a {y}",
        "what is the {x} of {y}",
        "how far is {y} from {y2}",
        "what's the population of {y}",
    ]
    xs = ["days", "weeks", "months", "hours", "minutes"]
    ys = ["week", "year", "month", "day"]
    for t in generic_templates[:2]:
        for x in xs:
            for y in ys:
                if x == y or (x=="days" and y=="day"):
                    continue
                u = t.format(x=x, y=y)
                out.append((cap(u), f"That depends on the exact units — let me know if you'd like the standard conversion for {x} in a {y}.", {}))
    extra = ["what's 15 percent of 200", "convert 10 kilometers to miles",
             "how many grams in a kilogram", "what's the square root of 144",
             "how many ounces in a pound", "convert 100 fahrenheit to celsius",
             "what's 7 times 8", "how many centimeters in a meter",
             "what's the exchange rate between usd and inr", "how many seconds in an hour",
             "what's 20 percent of 450", "convert 5 miles to kilometers",
             "how many milliliters in a liter", "what's the cube root of 27",
             "how many minutes in a day", "convert 32 celsius to fahrenheit",
             "what's 12 times 12", "how many millimeters in a centimeter",
             "what's 250 divided by 5", "how many weeks in a year"]
    extra_pool = expand_phrases(extra, ["", "quick question, ", "hey tara, "], ["", "?"], target=250)
    for u in extra_pool:
        out.append((cap(u), "Let me work that out for you based on standard conversions.", {}))
    return out

# ---------------- KNOWLEDGE ----------------
def gen_knowledge():
    templates = [
        "explain {t}", "explain {t} to me", "what is {t}", "can you explain {t}",
        "tell me about {t}", "i want to learn about {t}", "give me an overview of {t}",
        "how does {t} work", "define {t}", "what do you know about {t}",
        "can you break down {t} for me", "summarize {t} for me",
        "what exactly is {t}", "help me understand {t}",
        "give me a simple explanation of {t}",
        "what's the deal with {t}",
        "i keep hearing about {t}, what is it",
        "why does {t} matter",
        "give me the basics of {t}",
        "what should i know about {t}",
    ]
    out = []
    for t in templates:
        for topic in KNOWLEDGE_TOPICS:
            u = t.format(t=topic)
            resp = f"{cap(topic)} is a broad topic — here's a quick overview: it involves key concepts that build on fundamentals in its field. Want a deeper explanation or a simpler one?"
            out.append((cap(u), resp, {"topic": topic}))
    return out

# ---------------- STUDY ----------------
def gen_study():
    templates = [
        "help me study {s}", "explain {s} for my exam", "quiz me on {s}",
        "i have an exam on {s} tomorrow", "give me tips to study {s}",
        "can you help me revise {s}", "make a study plan for {s}",
        "what should i focus on in {s}", "give me a summary of {s}",
        "help me prepare for my {s} exam", "i'm struggling with {s}",
        "how do i improve in {s}", "give me practice questions on {s}",
        "explain the basics of {s}", "help me understand {s} concepts",
        "i need to study {s} for gate", "what topics are important in {s}",
        "create flashcards for {s}", "test my knowledge of {s}",
        "recommend resources to learn {s}",
        "what's the best way to learn {s}", "can you explain {s} with an example",
        "break {s} into simple steps for me", "i have a doubt in {s}",
        "what are common interview questions on {s}",
    ]
    responses = [
        "Sure! Let's break {s} down — want me to start with the fundamentals or go straight to the tricky parts?",
        "Happy to help with {s}. Should we go topic by topic or focus on a specific concept you're stuck on?",
        "Let's tackle {s} together. I can quiz you, summarize key topics, or explain specific concepts — what works best?",
        "Got it — studying {s}. Want a quick summary, a study plan, or some practice questions first?",
    ]
    out = []
    for t in templates:
        for s in STUDY_SUBJECTS:
            u = t.format(s=s)
            out.append((cap(u), random.choice(responses).format(s=s), {"subject": s}))
    return out

# ---------------- JOKE ----------------
def gen_joke():
    base = ["tell me a joke", "make me laugh", "say something funny", "got any jokes",
            "tell me something funny", "i need a laugh", "do you know any jokes",
            "cheer me up with a joke", "tell a joke", "i'm bored tell me a joke",
            "give me a joke", "can you be funny", "lighten the mood",
            "tell me a dad joke", "got a pun for me", "hit me with a joke",
            "make me smile", "tell me your best joke", "one more joke please"]
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the computer go to the doctor? It had a virus!",
        "I told my computer I needed a break, and now it won't stop sending me KitKats.",
        "Why do Java developers wear glasses? Because they don't see sharp!",
        "Why was the math book sad? It had too many problems.",
        "Why don't robots ever panic in emergencies? They have great circuit-breakers.",
        "I would tell you a joke about UDP, but you might not get it.",
        "Why did the student eat his homework? Because the teacher said it was a piece of cake.",
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the AI go to therapy? It had too many unresolved dependencies.",
        "Why was the cat afraid of the tree? Because of its bark!",
        "How does a penguin build its house? Igloos it together.",
        "Why did the coffee file a police report? It got mugged.",
        "Why do Python programmers wear glasses? Because they can't C.",
        "I asked my dog what's two minus two. He said nothing.",
    ]
    out = []
    for g in base:
        for suf in ["", "?", " tara"]:
            for topic in JOKE_TOPICS:
                u = f"{g}{topic}{suf}".strip()
                out.append((cap(u), random.choice(jokes), {}))
    return out

# ---------------- AFFIRMATION ----------------
def gen_affirmation():
    base = ["yes", "yeah", "yep", "yup", "sure", "of course", "absolutely",
            "definitely", "sounds good", "okay", "ok", "alright", "correct",
            "that's right", "exactly", "right", "for sure", "yes please",
            "sure thing", "yeah sure", "why not", "go ahead", "please do",
            "yes go ahead", "sounds great", "perfect, do it", "yes that's correct",
            "affirmative", "count me in", "i agree", "true", "that's true",
            "confirmed", "yes definitely", "yeah go for it", "okay do that",
            "yes i'm sure", "totally", "indeed"]
    responses = ["Great, got it!", "Perfect, moving forward with that.", "Okay, noted!",
                 "Alright, sounds good!", "Got it, thanks for confirming."]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_STATEMENT, target=650)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- NEGATION ----------------
def gen_negation():
    base = ["no", "nope", "nah", "no thanks", "not really", "no way", "never",
            "i don't think so", "not now", "no need", "negative", "not at all",
            "no, that's wrong", "incorrect", "that's not right", "i disagree",
            "false", "not interested", "no, cancel that", "nah i'm good",
            "no thank you", "not today", "i'd rather not", "no, don't",
            "please don't", "stop", "cancel", "nevermind", "forget it",
            "that's not correct", "no that's not what i meant", "not exactly",
            "no i don't want that"]
    responses = ["Okay, no worries!", "Got it, I'll skip that.", "Alright, cancelled.",
                 "Understood, no problem.", "Okay, noted — won't do that."]
    pool = expand_phrases(base, PREFIX_POOL_CASUAL, SUFFIX_POOL_STATEMENT, target=650)
    return [(cap(u), random.choice(responses), {}) for u in pool]

# ---------------- MOOD ----------------
def gen_mood():
    templates_neg = [
        "i'm feeling {m}", "i feel {m}", "i'm so {m} today", "i've been {m} lately",
        "today has been {m}", "i'm really {m} right now", "honestly i feel {m}",
        "i'm kind of {m}", "feeling pretty {m} today", "i'm a bit {m}",
        "i've been feeling {m} all week", "not gonna lie, i'm {m}",
        "lately i just feel {m}", "i woke up feeling {m}",
        "this whole week i've been {m}", "i can't shake this {m} feeling",
    ]
    templates_pos = templates_neg
    responses_neg = [
        "I'm sorry to hear that you're feeling {m}. Want to talk about what's going on, or would a distraction help?",
        "That sounds tough. Feeling {m} is hard — I'm here if you want to talk or need a break.",
        "Thanks for sharing that. Being {m} isn't easy — would it help to take a short break or talk it through?",
    ]
    responses_pos = [
        "That's great to hear you're feeling {m}! What's been going well?",
        "Love that energy! Glad you're feeling {m} today.",
        "That's wonderful — feeling {m} is a great place to be. Keep it up!",
    ]
    responses_neu = [
        "Got it, thanks for letting me know how you're feeling.",
        "Okay, noted. Let me know if there's anything I can help with.",
        "Thanks for sharing — I'm here if you want to talk more.",
    ]
    out = []
    for t in templates_neg:
        for m in MOODS_NEG:
            u = t.format(m=m)
            out.append((cap(u), random.choice(responses_neg).format(m=m), {"mood": m, "polarity": "negative"}))
    for t in templates_pos:
        for m in MOODS_POS:
            u = t.format(m=m)
            out.append((cap(u), random.choice(responses_pos).format(m=m), {"mood": m, "polarity": "positive"}))
    for t in templates_neg[:8]:
        for m in MOODS_NEU:
            u = t.format(m=m)
            out.append((cap(u), random.choice(responses_neu), {"mood": m, "polarity": "neutral"}))
    return out

# ---------------- UNKNOWN ----------------
def gen_unknown():
    responses = [
        "I'm not quite sure I understood that. Could you rephrase it?",
        "Hmm, I didn't quite catch that — can you say it differently?",
        "Sorry, I'm not sure what you mean. Could you try again?",
        "That's outside what I can help with right now — could you clarify?",
        "I'm not able to make sense of that input. Mind rewording it?",
    ]
    out = []
    gib_pool = expand_phrases(GIBBERISH, ["", "um, ", "hey tara, "], ["", "?", "!"], target=600)
    for u in gib_pool:
        out.append((u, random.choice(responses), {}))
    # out-of-scope but coherent sentences
    out_of_scope_base = OUT_OF_SCOPE_EXTRA + [
        "can you book me a flight to mars",
        "hack into my neighbor's wifi",
        "what's the meaning of life, the universe and everything",
        "translate this into klingon",
        "can you place an order for pizza right now",
        "predict tomorrow's lottery numbers",
        "can you control my smart home lights",
        "write my entire thesis for me by tonight",
        "can you send money to my friend",
        "diagnose this medical symptom for me",
        "give me legal advice for my court case",
        "can you turn off my alarm",
        "order me an uber",
        "can you make a phone call for me",
        "unlock my phone",
        "asdlkfj what is this even",
        "why is the sky green on tuesdays",
        "can you feel pain",
        "do aliens exist for real, prove it right now",
        "compute the meaning of purple",
    ]
    oos_pool = expand_phrases(out_of_scope_base, ["", "hey tara, ", "so, "], ["", "?"], target=400)
    for u in oos_pool:
        out.append((cap(u), random.choice(responses), {}))
    return out

# ----------------------------------------------------------------------
GENERATORS = {
    "GREETING": gen_greeting,
    "GOODBYE": gen_goodbye,
    "THANKS": gen_thanks,
    "HELP": gen_help,
    "ABOUT_TARA": gen_about,
    "SMALL_TALK": gen_small_talk,
    "TIME": gen_time,
    "DATE": gen_date,
    "WEATHER": gen_weather,
    "REMINDER": gen_reminder,
    "TASK": gen_task,
    "GENERAL_QUERY": gen_general_query,
    "KNOWLEDGE": gen_knowledge,
    "STUDY": gen_study,
    "JOKE": gen_joke,
    "AFFIRMATION": gen_affirmation,
    "NEGATION": gen_negation,
    "MOOD": gen_mood,
    "UNKNOWN": gen_unknown,
}

def build_dataset():
    rows = []
    stats = {}
    row_id = 1
    for intent, fn in GENERATORS.items():
        items = fn()
        # dedupe on utterance text (case-insensitive)
        seen = set()
        deduped = []
        for u, r, e in items:
            k = u.strip().lower()
            if k and k not in seen:
                seen.add(k)
                deduped.append((u, r, e))
        random.shuffle(deduped)
        if len(deduped) > TARGET_MAX:
            deduped = deduped[:TARGET_MAX]
        stats[intent] = len(deduped)
        for u, r, e in deduped:
            rows.append({
                "id": f"tara_{row_id:06d}",
                "intent": intent,
                "utterance": u,
                "response": r,
                "entities": e
            })
            row_id += 1
    return rows, stats

if __name__ == "__main__":
    rows, stats = build_dataset()
    print("Per-intent counts:")
    total = 0
    for k, v in stats.items():
        print(f"  {k:15s} {v}")
        total += v
    print(f"TOTAL: {total}")

    # JSONL
    with open("tara_dataset.jsonl", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Full JSON array
    with open("tara_dataset.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    # CSV (entities serialized as JSON string)
    with open("tara_dataset.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "intent", "utterance", "response", "entities"])
        for row in rows:
            writer.writerow([row["id"], row["intent"], row["utterance"], row["response"],
                              json.dumps(row["entities"], ensure_ascii=False)])

    with open("dataset_stats.json", "w") as f:
        json.dump({"per_intent_counts": stats, "total": total}, f, indent=2)
