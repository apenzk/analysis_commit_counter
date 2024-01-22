import requests
import matplotlib.pyplot as plt
import json
from datetime import datetime
from collections import defaultdict
from matplotlib.dates import YearLocator, DateFormatter

from config import access_token


# Replace with your GitHub organization and access token
organization = "Fantom-foundation"
number_of_repos = 1


def fetch_repo_commits_pagination(repo_url):
    commit_counts = defaultdict(int)

    while True:
        commits_response = requests.get(repo_url, headers={"Authorization": f"Bearer {access_token}"})
        commits = commits_response.json()

        # Extract commit dates
        dates = [commit["commit"]["author"]["date"] for commit in commits]

        # Convert ISO date strings to datetime objects
        dates = [datetime.strptime(date.split("T")[0], "%Y-%m-%d") for date in dates]

        # Count commits per month
        for date in dates:
            key = date.strftime("%Y-%m")
            commit_counts[key] += 1

        # Check for pagination
        link_header = commits_response.headers.get("Link")
        if link_header and 'rel="next"' in link_header:
            # There is a next page, update repo_url for the next request
            repo_url = link_header.split(';')[0][1:-1]
        else:
            # No more pages, break from the loop
            break

    return commit_counts


def plot_commit_history(commit_data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # oldest and latest date of the entire date range
    dates = list(commit_dates_data[0]["dates_months"].keys())
    dates.sort()
    oldest_date_str = dates[0]
    latest_date_str = dates[-1]
    # interpret the date as a year-month string
    oldest_date = datetime.strptime(oldest_date_str, "%Y-%m")
    latest_date = datetime.strptime(latest_date_str, "%Y-%m")
    print(oldest_date)

    # create a list of all months in the date range
    valid_months = []
    current_date = oldest_date
    while current_date <= latest_date:
        # write the current date to the list
        valid_months.append(current_date.strftime("%Y-%m"))
        if current_date.month == 12:
            # if the current month is december, set the month to january of the next year
            current_date = current_date.replace(year=current_date.year+1, month=1)
        else:
            # else just increment the month
            current_date = current_date.replace(month=current_date.month+1)

    print (valid_months)        
    # create a list of only january months
    january_months = []
    for i in range(len(valid_months)):
        if valid_months[i].endswith("-01"):
            january_months.append(valid_months[i])
    
    # for the first repo we add the months with value 0 to the dict
    for key in valid_months:
        if key not in commit_data[0]["dates_months"]:
            commit_data[0]["dates_months"][key] = 0

    for i in range(1, len(commit_data)):
        for key in valid_months:
            if key not in commit_data[i]["dates_months"]:
                commit_data[i]["dates_months"][key] = commit_data[i-1]["dates_months"][key]
            else:
                commit_data[i]["dates_months"][key] += commit_data[i-1]["dates_months"][key]


    for data in commit_dates_data:
        # sort the dict by key month
        data["dates_months"] = {k: v for k, v in sorted(data["dates_months"].items(), key=lambda item: item[0])}

        repo_name = data["repo"]
        commit_counts = data["dates_months"]
        total_commits = data["total_commits"]

        # Plot normal commit history
        ax1.plot(list(commit_counts.keys()), list(commit_counts.values()), label=f"{repo_name} (Total: {total_commits})", marker='')

        # Plot cumulative commit history
        cumulative_counts = [sum(list(commit_counts.values())[:i+1]) for i in range(len(commit_counts))]
        ax2.plot(list(commit_counts.keys()), cumulative_counts, label=f"{repo_name}", marker='')

    # from the keys create an array that only keeps the first month of a year
    january_months = []
    for i in range(len(valid_months)):
        if valid_months[i].endswith("-01"):
            january_months.append(valid_months[i])

    
        

    # Set labels and legend
    ax1.set_title(f'Commit History for {organization} Repositories')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Number of Commits')
    ax1.set_xticks(january_months)
    # ax1.legend()
    ax1.grid(True)

    ax2.set_title(f'Cumulative Commit History for {organization} Repositories')
    ax2.set_xlabel('Month')
    ax2.set_xticks(january_months)
    ax2.set_ylabel('Cumulative Number of Commits')
    # ax2.legend()
    ax2.grid(True)

    plt.savefig('commit_history.png')

    plt.show()


def save_total_commits_to_file(commit_data, filename="total_commits.json"):
    total_commits_data = {entry["repo"]: entry["total_commits"] for entry in commit_data}
    
    with open(filename, 'w') as file:
        json.dump(total_commits_data, file, indent=2)

# save commit data to file
def save_commit_data_to_file(commit_data, filename="commit_data.json"):
    with open(filename, 'w') as file:
        json.dump(commit_data, file, indent=2)

# ---------------------------- main ----------------------------

# Fetch all repositories in the organization
repos_url = f"https://api.github.com/orgs/{organization}/repos?per_page={number_of_repos}"
response = requests.get(repos_url, headers={"Authorization": f"Bearer {access_token}"})
repos = response.json()

# Print the response to inspect
print("... repos\n............................................")
for repo in repos:
    print(repo["name"])

# Fetch commit history for each repository
commit_dates_data = []
counter = 1
for repo in repos:
    repo_name = repo["name"]
    commits_url = f"https://api.github.com/repos/{organization}/{repo_name}/commits"
    commit_counts = fetch_repo_commits_pagination(commits_url)

    # Append repo_name, commit_counts, and total commits
    commit_dates_data.append({
        "repo": repo_name,
        "dates_months": commit_counts,
        "total_commits": sum(commit_counts.values())
    })
    print(f"... {counter} ............................................")
    print(commit_dates_data[-1])
    counter += 1


# After your loop that collects commit_data
save_total_commits_to_file(commit_dates_data, "total_commits.json")
save_commit_data_to_file(commit_dates_data, "commit_data.json")

plot_commit_history(commit_dates_data)

