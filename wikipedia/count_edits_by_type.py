# Count how many of a certain kind of contributions a user has made
# to a Wiki Project. Set a list of usernames, dates to check, what
# kinds of edits you care about, and how they can be identified from
# the edit summary.
# Note that checking revision tags isn't currently working - need to
# find a way to retrieve these as pywikibot's contributions class
# doesn't provide them.

from pywikibot import Site, User
from pywikibot.data import api
from datetime import datetime

# List all usernames you want to check
users = ["Avocadobabygirl"]

# Set a start and end date for the period you want to check
start_date = "20240901"
end_date = "20240930"

# Create categories for the types of edits you're interested in
# Under each category, list the summary and tag strings that will
# mark the edit as relevant
categories = {"sdc":
	              {"summary": ["Created claim:", "Changed label,"],
	               "tags": []
	               },
              "new_image":
	              {"summary": ["Uploaded a work"],
	               "tags": ["openrefine"]
	               },
              "edit_metadata":
	              {"summary": ["Changed an entity"],
	               "tags": []}
              }


# Connect to the Wiki Project you want to check with pywikibot
def connect_to_site():
	# For wikipedias, site_id should be formatted as "wikipedia:en"
	site_id = "commons"
	site = Site(site_id)
	return site


# Retrieve the contributions to this Project for all users
def check_user_activity(site):
	user_contributions = {k: [] for k in users}
	for username in users:
		contributions = retrieve_user_contributions(site, username)
		user_contributions[username] = contributions

	return user_contributions


# Get the contributions for a specific user
def retrieve_user_contributions(site, username):
	user = connect_to_user(site, username)
	start_datestamp = datetime.fromisoformat(start_date)
	end_datestamp = datetime.fromisoformat(end_date)
	# Reversed because you start at the present and work backwards
	contributions = api.ListGenerator(
		'usercontribs',
		site=site,
		parameters=dict(
			ucprop='ids|title|timestamp|comment|flags|tags',
			ucuser=username,
			ucstart=end_datestamp,
			ucend=start_datestamp,
		)
	)
	contributions.set_maximum_items(10000)

	return contributions


# Connect to the user with pywikibot
def connect_to_user(site, username):
	user = User(site, username)
	return user


# For each user analyse the retrieved contributions
def review_activity(activity):
	for username in activity.keys():
		user_report = analyse_user_activity(activity[username])
		print_report(username, user_report)


# Look at the edit summary of each contribution and see
# if any of the relevant strings appear
def analyse_user_activity(contributions):
	report = {k: [] for k in categories.keys()}
	for contribution in contributions:
		title = contribution['title']
		comment = contribution['comment']
		tags = "|".join(contribution['tags'])
		for cat in categories.keys():
			count = False
			for summary_string in categories[cat]["summary"]:
				if summary_string in comment:
					count = True
			for tag_string in categories[cat]["tags"]:
				if tag_string in tags:
					count = True

			if count:
				report[cat].append(title)

	return report


# Print each username and how many of each category of edit they made
def print_report(username, report):
	print(username)
	for cat in report.keys():
		print("{c}: {n}".format(c=cat, n=len(report[cat])))


def run():
	site = connect_to_site()
	activity = check_user_activity(site)
	review_activity(activity)


if __name__ == '__main__':
	run()
