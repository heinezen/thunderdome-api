# Thunderdome API Scripts

Scripts for automating work with the API of the [Thunderdome](https://github.com/StevenWeathers/thunderdome-planning-poker) Planning Poker service.

## Basic Usage

### Poker Games

#### Creating Games from GitLab Items

You need the following information to run the script:

- `API_KEY`: API Key for Thunderdome. You can generate it in your [profile](https://thunderdome.dev/profile).
- `GITLAB_TOKEN`: Personal Access Token for GitLab which can be added in your [Preferences](https://gitlab.com/-/user_settings/personal_access_tokens). You need at least scope `api`.

Example script usage:

```bash
python3 main.py game \
                create \
                API_KEY \
                GITLAB_TOKEN \
                --auto-finish \
                --join-password 1234 \
                --leader-password 5678 \
                --teamid abababa-1337-2342-1406-deadbeef \
                --allowed-values 0 1 2 3 5 8 13 20 40 100 \? ☕️ \
                --issues https://gitlab.example.com/test-orga/thunderdome/-/issues/1 ... \
                --milestones https://gitlab.example.com/groups/test-orga/-/milestones/1 ... \
                --iterations https://gitlab.example.com/groups/test-orga/-/cadences/12345/iterations/12345 ... \
                --epics https://gitlab.example.com/groups/test-orga/-/epics/1 ... \
                --projects https://gitlab.example.com/test-orga/thunderdome ...
```

#### Updating Existing Games from GitLab Items

You need the following information to run the script:

- `GAME_ID`: ID of the Thunderdome game. Visible in the URL, e.g.

```
https://thunderdome.dev/game/abababa-1337-2342-1406-deadbeef
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Game ID
```

- `API_KEY`: API Key for Thunderdome. You can generate it in your [profile](https://thunderdome.dev/profile).
- `GITLAB_TOKEN`: Personal Access Token for GitLab which can be added in your [Preferences](https://gitlab.com/-/user_settings/personal_access_tokens). You need at least scope `api`.

Example script usage:

```bash
python3 main.py game \
                update \
                GAME_ID \
                API_KEY \
                GITLAB_TOKEN \
                --issues https://gitlab.example.com/test-orga/thunderdome/-/issues/1 ... \
                --milestones https://gitlab.example.com/groups/test-orga/-/milestones/1 ... \
                --iterations https://gitlab.example.com/groups/test-orga/-/cadences/12345/iterations/12345 ... \
                --epics https://gitlab.example.com/groups/test-orga/-/epics/1 ... \
                --projects https://gitlab.example.com/test-orga/thunderdome ...
```

#### Transferring Story Points to GitLab

To transfer story points from a thunderdome planning poker session, follow these steps:

1. In your Thunderdome game: Set links for all stories.
2. Get the information required to run the script.
   - `GAME_ID`: ID of the Thunderdome game. Visible in the URL, e.g.

```
https://thunderdome.dev/game/abababa-1337-2342-1406-deadbeef
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Game ID
```

   - `API_KEY`: API Key for Thunderdome. You can generate it in your [profile](https://thunderdome.dev/profile).
   - `GITLAB_TOKEN`: Personal Access Token for GitLab which can be added in your [Preferences](https://gitlab.com/-/user_settings/personal_access_tokens). You need at least scope `api`.
3. Run the script:

```bash
python3 main.py game fetch <GAME_ID> <API_KEY> <GITLAB_TOKEN>
```

### Storyboards

#### Assigning an Iteration to linked GitLab Items

To assign a GitLab iteration to linked issues in stories from a Thunderdome storyboard, follow these steps:

1. In your Thunderdome storyboard: Set links for all stories.
2. Get the information required to run the script.
   - `BOARD_ID`: ID of the Thunderdome storyboard. Visible in the URL, e.g.

```
https://thunderdome.dev/storyboard/1670f90b-61d3-427c-ac07-bfaa8d21fad1
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Board ID
```

   - `ITERATION_LINK`: Link to the GitLab iteration that linked issues should be assigned to.
   - `API_KEY`: API Key for Thunderdome. You can generate it in your [profile](https://thunderdome.dev/profile).
   - `GITLAB_TOKEN`: Personal Access Token for GitLab which can be added in your [Preferences](https://gitlab.com/-/user_settings/personal_access_tokens). You need at least scope `api`.

Example script usage:

```bash
python3 main.py storyboard \
                fetch \
                BOARD_ID \
                ITERATION_LINK \
                API_KEY \
                GITLAB_TOKEN \
                --filter-goals Common ... \
                --filter-columns Picked ... \
                --cleanup-iteration
```
