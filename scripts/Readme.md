# Scripts Documentation

## update_issue_status.sh

### Description

`update_issue_status.sh` is a Bash script that updates the status of a GitHub issue across all associated projects. It utilizes the GitHub CLI (`gh`) to interact with GitHub's GraphQL API.

### Prerequisites

- **GitHub CLI (`gh`)**: Ensure that the GitHub CLI is installed and authenticated. You can download it from [here](https://cli.github.com/).
- **Permissions**: The authenticated user must have access to the repository and associated projects.

### Usage

```bash
./update_issue_status.sh --owner OWNER --repo REPO --issue-number ISSUE_NUMBER --new-status NEW_STATUS
```

#### Parameters

- `--owner`: The GitHub username or organization that owns the repository.
- `--repo`: The name of the repository containing the issue.
- `--issue-number`: The number of the issue to update.
- `--new-status`: The new status to set for the issue in all associated projects.

#### Example

```bash
./update_issue_status.sh --owner NethServer --repo dev --issue-number 123 --new-status Verified
```

### How It Works

1. **Argument Parsing**: The script parses command-line arguments to obtain the required parameters.
2. **Authentication**: Checks for the presence of the `gh` CLI and ensures it is authenticated.
3. **Retrieve Issue Node ID**: Uses GraphQL queries to fetch the node ID of the specified issue.
4. **Fetch Associated Projects**: Retrieves a list of all projects that the issue is associated with.
5. **Update Status in Projects**:
   - For each project:
     - Retrieves the item ID corresponding to the issue.
     - Finds the ID of the `Status` field.
     - Obtains the option ID for the desired new status.
     - Updates the issue's status in the project using a GraphQL mutation.
6. **Completion**: Outputs the status of each update and completes execution.

### Output

The script provides informative output at each step, including:

- Confirmation of parsed arguments.
- IDs retrieved for the issue, projects, fields, and options.
- Success or warning messages during the update process.

### Error Handling

- **Missing Arguments**: The script checks for all required arguments and displays usage instructions if any are missing.
- **Authentication Errors**: If the `gh` CLI is not installed or authenticated, the script exits with an error message.
- **GraphQL API Failures**: Errors in API calls are caught, and appropriate messages are displayed.

### Notes

- The script assumes that the `Status` field exists in the associated projects and that the `NEW_STATUS` provided is a valid option.
- If the `NEW_STATUS` is not found in a project's status options, the script will issue a warning and continue to the next project.
- Ensure that the `gh` CLI has the necessary scopes and permissions to perform the operations.
