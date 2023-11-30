# Script used at Te Papa to combine data exported from
# both EMu and our API to create a dataset that can
# be used in Mix n Match. Te Papa's agent data is found
# at https://mix-n-match.toolforge.org/#/catalog/6094
# This script is for demonstration use and is presented
# without any warranty.

import csv
from tqdm import tqdm

api_data_file = "apiagentexport.csv"
emu_data_file = "emupartiesexport.csv"

output_file = "tepapa-agents-mixandmatch.csv"

stored_data = {}


def save_from_api():
    # Store data from the API
    with open(api_data_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")

        for row in reader:
            irn = row["pid"].split("/")[-1]
            wikidataQID = row["wikidataQID"].split("/")[-1]
            title = row["title"]
            givenName = row["givenName"]
            familyName = row["familyName"]
            gender = row["gender"]
            if gender:
                gender = map_gender(gender)
            born = row["birthDate"]
            died = row["deathDate"]
            birthPlace = row["birthPlace"]
            deathPlace = row["deathPlace"]
            orcidID = row["orcidID"].split("/")[-1]
            ethnicity = row["ethnicity"]
            nationality = row["nationality"]

            url = "https://collections.tepapa.govt.nz/agent/{}".format(irn)

            isReferencedBy = row["isReferencedBy"]

            stored_data.update({irn: {
                "q": wikidataQID,
                "type": "Q5",
                "name": title,
                "givenName": givenName,
                "familyName": familyName,
                "P21": gender,
                "born": born,
                "died": died,
                "birthPlace": birthPlace,
                "deathPlace": deathPlace,
                "P496": orcidID,
                "nationality": nationality,
                "iwiEthnicGroup": ethnicity,
                "url": url,
                "isReferencedBy": isReferencedBy
            }})

    print("API data loaded")


def save_from_emu():
    # If IRN is already stored, add extra data from EMu
    emu_source_fieldnames = ["PartiesIrn", "First", "Middle", "Last", "Specialities", "Label", "Type", "NumberIdentifier", "AssociatedWithIrn", "AssociatedWithDisplayName", "AssociatedWithRole", "WebAssociationsWeb", "WebAssociationsDisplayText", "PlaceOfActivity", "CulturalInfluences", "Location", "SynonymsIrn", "SynonymsDisplayName"]

    with open(emu_data_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")

        for row in reader:
            irn = row["PartiesIrn"]
            if irn in stored_data.keys():
                first_name = row["First"]
                middle_name = row["Middle"]
                family_name = row["Last"]
                roles = row["Role"]
                specialities = row["Specialities"]
                label = row["Label"]
                identifier_types = row["Type"]
                identifiers = row["NumberIdentifier"]
                date_from = row["DateFrom"]
                date_to = row["DateTo"]
                associated_ids = row["AssociatedWithIrn"]
                associated_names = row["AssociatedWithDisplayName"]
                associated_roles = row["AssociatedWithRole"]
                web_links = row["WebAssociationsWeb"]
                web_text = row["WebAssociationsDisplayText"]
                activity_location = row["PlaceofActivity"]
                cultural_influences = row["CulturalInfluences"]
                locations = row["Location"]
                synonym_irns = row["SynonymsIrn"]
                synonym_names = row["SynonymsDisplayName"]

                if identifiers:
                    store_main_identifiers(irn, identifiers, identifier_types)
                    other_identifiers = zip_columns(identifiers, identifier_types)
                else:
                    other_identifiers = None

                stored_data[irn].update({
                    "middleName": middle_name,
                    "roles": roles,
                    "specialities": specialities,
                    "label": label,
                    "identifierTypes": identifier_types,
                    "identifiers": identifiers,
                    "otherIdentifiers": other_identifiers,
                    "activeFrom": date_from,
                    "activeTo": date_to,
                    "associatedIDs": associated_ids,
                    "associatedNames": associated_names,
                    "associatedRoles": associated_roles,
                    "webLinks": web_links,
                    "webText": web_text,
                    "activityLocation": activity_location,
                    "culturalInfluences": cultural_influences,
                    "locations": locations,
                    "synonymIDs": synonym_irns,
                    "synonymNames": synonym_names,
                })

    print("EMu data loaded")


def store_main_identifiers(irn, identifiers, identifier_types):
    identifiers = identifiers.split("|")
    identifier_types = identifier_types.split("|")
    for i in range(len(identifiers)):
        try:
            id_type = identifier_types[i]
            if id_type == "ULAN (Union List of Artists Names)":
                stored_data[irn].update({"P245": identifiers[i]})
            elif id_type == "IPNI (International Plant Names Index)":
                ipni_id = identifiers[i]
                if ipni_id.startswith("urn:"):
                    ipni_id = ipni_id.split(":")[-1]
                stored_data[irn].update({"P586": ipni_id})
            elif id_type == "VIAF (Virtual International Authority File)":
                stored_data[irn].update({"P214": identifiers[i]})
        except IndexError:
            print(irn)
            print(identifiers, identifier_types)

def generate_descriptions():
    # Give each record a formatted description
    for irn in stored_data.keys():
        agent_data = stored_data[irn]
        description = format_description(agent_data)
        if description:
            stored_data[irn].update({"description": description})

    print("Descriptions created")


def format_description(record):
    # Collate various fields (if available) into a readable description
    description_values = []

    # Concatenate full name
    names = []
    if record.get("givenName"):
        names.append(record["givenName"])
    if record.get("middleName"):
        names.append(record["middleName"])
    if record.get("familyName"):
        names.append(record["familyName"])
    if len(names) > 0:
        description_values.append(" ".join(names))

    if record.get("synonymNames"):
        description_values.append("Also known as: {}".format(split_and_join(record["synonymNames"])))

    # Include short summary
    if record.get("label"):
        description_values.append(record["label"])

    # Include place of birth and death
    if record.get("birthPlace"):
        description_values.append("Born {}".format(record["birthPlace"]))
    if record.get("deathPlace"):
        description_values.append("Died {}".format(record["deathPlace"]))

    # Concatenate any roles assigned
    if record.get("roles"):
        description_values.append(split_and_join(record["roles"]))

    # Include nationality and iwi/hapū/ethnicity
    if record.get("nationality"):
        description_values.append("Nationality: {}".format(split_and_join(record["nationality"])))
    if record.get("iwiEthnicGroup"):
        description_values.append("Iwi or hapū/ethnicity: {}".format(split_and_join(record["iwiEthnicGroup"])))

    # Include collated identifiers
    if record.get("otherIdentifiers"):
        description_values.append("Other identifiers: {}".format(record["otherIdentifiers"]))

    if len(description_values) > 0:
        description = ". ".join(description_values)
    else:
        description = None

    return description


def split_and_join(value):
    split_values = value.split("|")
    joined_values = "; ".join(split_values)
    return joined_values


def export_combined_data():
    # Pull from stored data to write out each record in mix n match-friendly format
    # Fields are: id, Known QID, Type=Human (Q5), title, formatted description, birthDate, deathDate, gender,
    # ORCID ID, VIAF ID, ULAN ID, IPNI ID, url
    # And then fields for the reference version
    fieldnames = ["id", "q", "type", "name", "description", "born", "died", "P21", "P496", "P214", "P245", "P586", "url", "activeFrom", "activeTo", "roles", "specialities", "otherIdentifiers", "associatedParties", "roles", "nationality", "iwiEthnicGroup", "culturalInfluences", "locations", "synonyms"]

    write_file = open(output_file, "w", newline="", encoding="utf-8")
    writer = csv.writer(write_file, delimiter=",")
    writer.writerow(fieldnames)

    print("Ready to write csv")

    for irn in tqdm(stored_data.keys(), desc="Writing agents"):
        agent_data = stored_data[irn]
        row_values = []
        for field in fieldnames:
            write_value = None
            if field == "id":
                write_value = irn
            elif field == "associatedParties":
                if agent_data.get("associatedNames") and agent_data.get("associatedIDs"):
                    write_value = zip_columns(agent_data["associatedNames"], agent_data["associatedIDs"])
                else:
                    write_value = agent_data.get("associatedNames")
            elif field == "synonyms":
                if agent_data.get("synonymNames") and agent_data.get("synonymIDs"):
                    write_value = zip_columns(agent_data["synonymNames"], agent_data["synonymIDs"])
                else:
                    write_value = agent_data.get("synonymNames")
            else:
                write_value = agent_data.get(field)

            if not write_value:
                write_value = ""

            row_values.append(write_value)

        writer.writerow(row_values)

    write_file.close()

    print("Output csv completed")


def zip_columns(col_a, col_b):
    # Zip two columns to combine related values
    if len(col_a) > 0 or len(col_b) > 0:
        col_a_split = col_a.split("|")
        col_b_split = col_b.split("|")
        if len(col_a_split) == len(col_b_split):
            if len(col_a_split) > 0:
                zipped_cols = zip(col_a_split, col_b_split)
                formatted_cols = ["{a} ({b})".format(a=i[0], b=i[1]) for i in zipped_cols]
                return "; ".join(formatted_cols)
        else:
            return "{a}: {b}".format(a=col_a, b=col_b)

    return None


def map_gender(gender):
    # Convert gender values to QID items
    if gender == "Male":
        return "Q6581097"
    elif gender == "Female":
        return "Q6581072"
    elif gender == "Gender Diverse":
        return "Q48270"


def run():
    save_from_api()
    save_from_emu()
    generate_descriptions()
    export_combined_data()


if __name__ == "__main__":
    run()
