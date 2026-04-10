import psycopg2
from collections import defaultdict
from graphviz import Digraph

# ---------------------------------
# PostgreSQL connection
# ---------------------------------

conn = psycopg2.connect(
    host="localhost",
    database="family_tree",
    user="postgres",
    password="post1234"
)

cur = conn.cursor()

# ---------------------------------
# Create graph
# ---------------------------------

dot = Digraph("FamilyTree", format="svg")
dot.attr(rankdir="TB")
dot.attr(splines="ortho")
dot.attr(nodesep="0.6")
dot.attr(ranksep="1.0")
dot.attr(bgcolor="white")

dot.attr(
    "node",
    shape="box",
    style="rounded,filled",
    fontname="Helvetica",
    fontsize="10"
)

dot.attr(
    "edge",
    arrowhead="none"
)
dot.attr(newrank="true")

# ---------------------------------
# Load all people
# ---------------------------------

cur.execute("""
    SELECT prsn_id, first_nm, last_nm, gender, death_dt
    FROM gupta.master
""")

people = {}

for prsn_id, first_nm, last_nm, gender, death_dt in cur.fetchall():

    last_nm = "" if last_nm == "-" else last_nm
    full_name = f"{first_nm} {last_nm}".strip()

    if gender == "M":
        fillcolor = "lightblue"
    elif gender == "F":
        fillcolor = "lightpink"
    else:
        fillcolor = "lightgrey"

    label = full_name

    if death_dt is not None:
        label = f"✝ {full_name}"

    people[prsn_id] = {
        "name": label,
        "gender": gender,
        "death_dt": death_dt
    }

    dot.node(
        str(prsn_id),
        label=label,
        fillcolor=fillcolor,
        color="gray40" if death_dt is not None else "black",
        penwidth="2" if death_dt is not None else "1"
    )

# ---------------------------------
# Load marriages
# ---------------------------------

cur.execute("""
    SELECT couple_id, husband_id, wife_id
    FROM gupta.marriage
""")

couples = {}
children_by_couple = defaultdict(list)

for couple_id, husband_id, wife_id in cur.fetchall():
    couples[couple_id] = {
        "husband": husband_id,
        "wife": wife_id
    }

# ---------------------------------
# Load children
# ---------------------------------

cur.execute("""
    SELECT relation_id, child_id, couple_id
    FROM gupta.children
""")

for relation_id, child_id, couple_id in cur.fetchall():
    children_by_couple[couple_id].append(child_id)

# ---------------------------------
# Build family clusters
# ---------------------------------

for couple_id, data in couples.items():

    husband_id = data["husband"]
    wife_id = data["wife"]
    children = children_by_couple.get(couple_id, [])

    family_node = f"family_{couple_id}"

    with dot.subgraph(name=f"cluster_{couple_id}") as c:
        c.attr(style="invis")


        family_node = f"family_{couple_id}"

        c.node(
            family_node,
            label="",
            shape="point",
            width="0.01",
            height="0.01",
        )
        
        # Put family node below spouses
        

        # Husband + wife same row
        with c.subgraph() as spouses:
            spouses.attr(rank="same")
            spouses.node(str(husband_id))
            spouses.node(family_node)   
            spouses.node(str(wife_id))
            spouses.edge(f"{husband_id}:e", f"{family_node}:w")
            spouses.edge(f"{wife_id}:w", f"{family_node}:e")


        # Children same row
        with c.subgraph() as child_rank:
            child_rank.attr(rank="same")

            for child_id in children:
                child_rank.node(str(child_id))
                c.edge(family_node, str(child_id))

# ---------------------------------
# Export
# ---------------------------------

output_filename = "family_tree"
dot.render(output_filename, cleanup=True)

print(f"Family tree saved as {output_filename}.svg")

cur.close()
conn.close()