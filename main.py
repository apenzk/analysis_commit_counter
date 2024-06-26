import requests
import matplotlib.pyplot as plt
import json
from datetime import datetime
from collections import defaultdict
from matplotlib.dates import YearLocator, DateFormatter

from config import access_token
from config import organization

# Max number of repositories to fetch. Might have to limit this to make it work.
number_of_repos = 500


def fetch_repo_commits_pagination(repo_url):
    commit_counts = defaultdict(int)

    while True:
        commits_response = requests.get(repo_url, headers={"Authorization": f"Bearer {access_token}"})
        commits = commits_response.json()

        # Extract commit dates
        dates = []
        try:
            for commit in commits:
                dates.append(commit["commit"]["author"]["date"])
        except:
            print("Error")
            print(commits)
            # skip this repo and go to the next one
            break

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

    # sort the dict by key month
    commit_counts = {k: v for k, v in sorted(commit_counts.items(), key=lambda item: item[0])}

    return commit_counts


def plot_commit_history(commit_data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # oldest and latest date of all repos
    oldest_date = None
    latest_date = None
    for data in commit_data:
        dates = list(data["dates_months"].keys())
        dates.sort()
        if len(dates) == 0:
            continue
        oldest_date_str_current = dates[0]
        latest_date_str_current = dates[-1]
        # interpret the date as a year-month string
        oldest_date_current = datetime.strptime(oldest_date_str_current, "%Y-%m")
        latest_date_current = datetime.strptime(latest_date_str_current, "%Y-%m")
        if oldest_date == None or oldest_date_current < oldest_date:
            oldest_date = oldest_date_current
        if latest_date == None or latest_date_current > latest_date:
            latest_date = latest_date_current

    print("oldest_date")
    print (oldest_date)
    print("latest_date")
    print (latest_date)


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


    for data in commit_dates_data :

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

def get_commit_dates():
    # Fetch all repositories in the organization
    bool_next_page = True
    page = 1
    repos = []
    while bool_next_page:
        repos_url = f"https://api.github.com/orgs/{organization}/repos?per_page={number_of_repos}&page={page}"
        response = requests.get(repos_url, headers={"Authorization": f"Bearer {access_token}"})
        repos_current = response.json()
        if len(repos_current) == 0:
            bool_next_page = False
        else:
            repos.extend(repos_current)
            page += 1

    # Print the response to inspect
    print("... repos\n............................................")
    for repo in repos:
        print(repo["name"])
    print(f"Total number of repositories: {len(repos)}")

    # keep only number_of_repos repos
    if len(repos) > number_of_repos:
        repos = repos[:number_of_repos]
        print(f"Reduced total number of repositories: {len(repos)}")

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

    return commit_dates_data

def get_commit_dates_from_file(filename="commit_data.json"):
    with open(filename, 'r') as file:
        commit_dates_data = json.load(file)
    return commit_dates_data

# ---------------------------- main ----------------------------


commit_dates_data = get_commit_dates()
# commit_dates_data = get_commit_dates_from_file()

# After your loop that collects commit_data
save_total_commits_to_file(commit_dates_data, "total_commits.json")
save_commit_data_to_file(commit_dates_data, "commit_data.json")

plot_commit_history(commit_dates_data)

