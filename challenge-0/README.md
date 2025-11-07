# 1. Environment Creation and Resources Deployment

**Expected Duration:** 30 minutes

Welcome to your very first challenge! Your goal in this challenge is to create the services and enviornment necessary to conduct this hackathon. You will deploy the required resources in Azure, create your development enviornment and all the assets necessary for the subsequent challenges. By completing this challenge, you will set up the foundation for the rest of the hackathon.

If something is not working correctly, please do let your coach know!

## 1.1 Fork the Repository

Before you start, please fork this repository to your GitHub account by clicking the `Fork` button in the upper right corner of the repository's main screen (or follow the [documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository)). This will allow you to make changes to the repository and save your progress.

## 1.2 Development Environment

GitHub Codespaces is a cloud-based development environment that allows you to code from anywhere. It provides a fully configured environment that can be launched directly from any GitHub repository, saving you from lengthy setup times. You can access Codespaces from your browser, Visual Studio Code, or the GitHub CLI, making it easy to work from virtually any device.

To open GitHub Codespaces, click on the button below:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/)

Please select your forked repository from the dropdown and, if necessary, adjust other settings of GitHub Codespace.

**NOTE:** If GitHub Codespaces is not enabled in your organization, you can enable it by following the instructions [here](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/enabling-or-disabling-github-codespaces-for-your-organization), or, if you cannot change your GitHub organization's settings, create a free personal GitHub account [here](https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F&source=header-home). The Github Free Plan includes 120 core hours per month, equivalent to 60 hours on a 2-core machine, along with 15 GB of storage.

## 1.3 Resource Deployment Guide

We're now using the [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/) to deploy the environment defined in `challenge-0/azure.yaml`. The Bicep template that provisions every resource lives in `challenge-0/infra/main.bicep`.

### Prerequisites

- Install the Azure CLI and Azure Developer CLI (`azd`).
- Ensure you have the required Azure permissions to create resources and role assignments in your subscription.

### Deploy with azd

From the repository root, run the following commands:

```powershell
azd auth login
azd env new <environment-name> --location swedencentral
azd up
```

- Replace `<environment-name>` with a friendly name (for example, `hackathon`).
- The `azd env new` command seeds environment configuration and prompts for the subscription and resource group name. The default location (`swedencentral`) aligns with the template.
- Create a new resource group when prompted (for example, `rg-aihackaton-<abc>` where `abc` are the first three letters of your last name).

The deployment usually completes within 10 minutes and creates all dependent role assignments automatically. If the deployment fails due to a missing resource provider (for example, `Microsoft.AlertsManagement`), register it and re-run `azd up`.

## 1.4 Verify the creation of your resources

Go back to your `Azure Portal` and find your `Resource Group` that should by now contain the storage account, Azure AI Foundry hub and project, Azure AI Search, Cosmos DB (serverless), Container Registry, Log Analytics workspace with Application Insights, and a Key Vault.

![alt text](image.png)

## 1.5 Let's retrieve the necessary keys

After deploying the resources, you will need to configure the environment variables in the `.env` file. Double check you have logged in into your Azure account on the CLI. If that's settled, let's move into retrieving our keys. The `.env` file is a configuration file that contains the environment variables for the application. The `.env` file is automatically created by running the following command within the terminal in your Codespace.

**Then run the get-keys script with your resource group name:**

```bash
cd challenge-0 && ./get-keys.sh --resource-group YOUR_RESOURCE_GROUP_NAME
```

Replace `YOUR_RESOURCE_GROUP_NAME` with the actual name of the resource group created on step 1.3.

This script will connect to Azure and fetch the necessary keys and populate the `.env` file with the required values in the root directory of the repository.

## 1.6 Verify `.env` setup

When the script is finished, review the `.env` file to ensure that all the values are correct. If you need to make any changes, you can do so manually.

The repo has an `.env.sample` file that shows the relevant environment variables that need to be configured in this project. The script should create a `.env` file that has these same variables _but populated with the right values_ for your Azure resources.

If the file is not created, simply copy over `.env.sample` to `.env` - then populate those values manually from the respective Azure resource pages using the Azure Portal.

## Conclusion

By reaching this section you should have every resource and installed the requirements necessary to conduct the hackathon. In the next challenges, you will use these services to start strongly your Azure AI Agents journey.

Now the real fun begins!
