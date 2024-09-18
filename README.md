# Thunderdome API Scripts

Scripts for automating work with the API of the [Thunderdome](https://github.com/StevenWeathers/thunderdome-planning-poker) Planning Poker service.

## Basic Usage

### Transferring Story Points to GitLab

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

```
python3 main.py fetch <GAME_ID> <API_KEY> <GITLAB_TOKEN>
```