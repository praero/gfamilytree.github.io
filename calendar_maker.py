from ics.alarm import DisplayAlarm
import psycopg2
from ics import Calendar, Event
from datetime import datetime, timedelta, date, timezone
from ics.grammar.parse import ContentLine

def get_ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        # Use a dictionary to match the last digit
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def event_date_this_year(source_date):
    today = date.today()
    try:
        candidate = source_date.replace(year=today.year)
    except ValueError:
        # Feb 29 fallback for non-leap year
        candidate = source_date

    return candidate

now_tz = datetime.now(timezone(timedelta(hours=4))).strftime("%Y%m%dT%H%M%S%Z")


# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    database="family_tree",
    user="postgres",
    password="post1234"
)

cur = conn.cursor()

calendar = Calendar()

# -----------------------------
# Birthdays
# -----------------------------

cur.execute("""
    SELECT *
    FROM gupta.calendar_maker
""")

for row in cur.fetchall():
    (first_nm,last_nm,birth_dt, father_nm, mother_nm, numchild,hash_key,dtstamp) = row
    if last_nm == '-':
        full_nm = first_nm
    else:
        full_nm = f"{first_nm} {last_nm}"

    event = Event()

    event.name = f"🎂 Birthday: {full_nm}"
    event.begin = event_date_this_year(birth_dt)
    event.make_all_day()
    event.extra.append(ContentLine(name="RRULE", value="FREQ=YEARLY"))
    event.extra.append(ContentLine(name="DTSTAMP",value=dtstamp.strftime("%Y%m%dT%H%M%S%Z")))
    event.extra.append(ContentLine(name="LAST-MODIFIED", value=now_tz))

    event.uid = f'{hash_key}-birthday@family_calendar.gu'
    if numchild is not None:
        event.description = f'Birthday of {first_nm}, {get_ordinal(numchild)} child of {father_nm}-{mother_nm}'
    else:
        event.description = f"Birthday of {first_nm}"  

    event.alarms.append(
        DisplayAlarm(
            trigger=timedelta(hours=12)
        )
    )
    
    calendar.events.add(event)

# -----------------------------
# Anniversaries
# -----------------------------

cur.execute("""
    SELECT *
    FROM gupta."MarriedCoupleData"
""")

for row in cur.fetchall():
    (
        couple_id,
        husband_name,
        wife_name,
        last_nm,
        anniversary,
        next_num,
        num_child,
        marriage_date,
        hash_key,
        dtstamp
    ) = row

    if last_nm == '-':
        couple_name = f"{husband_name} & {wife_name}"
    else:
        couple_name = f"{husband_name} & {wife_name} {last_nm}"

    event = Event()
    event.name = f"💍 Anniversary: {couple_name}"
    event.begin = event_date_this_year(marriage_date)
    event.make_all_day()
    event.uid = f'{hash_key}-anniversary@family_calendar.gu'
    event.description = f"Wedding anniversary of {couple_name}, married in {marriage_date.year}"

    event.extra.append(ContentLine(name="RRULE", value="FREQ=YEARLY"))
    event.extra.append(ContentLine(name="DTSTAMP",value=dtstamp.strftime("%Y%m%dT%H%M%S%Z")))
    event.extra.append(ContentLine(name="LAST-MODIFIED", value=now_tz))

    event.alarms.append(
        DisplayAlarm(
            trigger=timedelta(hours=12)
        )
    )

    calendar.events.add(event)

# -----------------------------
# Export ICS File
# -----------------------------

with open("family_calendar.ics", "w", encoding="utf-8") as f:
    f.writelines(calendar)

cur.close()
conn.close()

print("family_calendar.ics created successfully")