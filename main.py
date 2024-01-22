import requests
import matplotlib.pyplot as plt
import json
from datetime import datetime
from collections import defaultdict
from matplotlib.dates import YearLocator, DateFormatter

from config import access_token


# Replace with your GitHub organization and access token
organization = "Fantom-foundation"
number_of_repos = 2


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
    # dates = list(commit_dates_data[0]["dates_months"].keys())
    # dates.sort()
    # oldest_date = dates[0]
    # latest_date = dates[-1]

    # # oldest and latest date of the entire date range
    # dates = list(commit_dates_data[0]["dates_months"].keys())
    # dates.sort()
    # oldest_date = dates[0]
    # latest_date = dates[-1]
    # # create a valid month list between the first and last month
    # # dont use strftime, but keep the datetime object
    # valid_months = []
    # january_months = []
    # for date in range(oldest_date.month, latest_date.month+1):
        

    # collector for the month keys
    valid_months = []    
    for data in commit_data:
        for key, value in data["dates_months"].items():
            if key not in valid_months:
                valid_months.append(key)
    valid_months.sort()
    print(valid_months)

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
        print (data)
        # sort the dict by key month
        data["dates_months"] = {k: v for k, v in sorted(data["dates_months"].items(), key=lambda item: item[0])}
        print (data)

        repo_name = data["repo"]
        commit_counts = data["dates_months"]
        total_commits = data["total_commits"]

        # Plot normal commit history
        ax1.plot(list(commit_counts.keys()), list(commit_counts.values()), label=f"{repo_name} (Total: {total_commits})", marker='')

        # Plot cumulative commit history
        cumulative_counts = [sum(list(commit_counts.values())[:i+1]) for i in range(len(commit_counts))]
        ax2.plot(list(commit_counts.keys()), cumulative_counts, label=f"{repo_name}", marker='')



    # Set labels and legend
    ax1.set_title(f'Commit History for {organization} Repositories')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Number of Commits')
    # ax1.legend()
    ax1.grid(True)

    ax2.set_title(f'Cumulative Commit History for {organization} Repositories')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Cumulative Number of Commits')
    # ax2.legend()
    ax2.grid(True)

    plt.show()


def save_total_commits_to_file(commit_data, filename="total_commits.json"):
    total_commits_data = {entry["repo"]: entry["total_commits"] for entry in commit_data}
    
    with open(filename, 'w') as file:
        json.dump(total_commits_data, file, indent=2)

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
    print("...............................................")
    print(commit_dates_data)


# After your loop that collects commit_data
save_total_commits_to_file(commit_dates_data, "total_commits.json")

plot_commit_history(commit_dates_data)

