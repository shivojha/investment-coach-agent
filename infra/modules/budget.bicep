// Azure Cost Management — Budget Alert
// Cost: FREE — budget alerts are free to configure
// Alerts when spend approaches or exceeds threshold
// Scope: resource group — only tracks investment-coach resources

@description('Monthly budget threshold in USD')
param monthlyBudgetUsd int = 15   // alert well above expected ~$1/month

@description('Email address to send alerts to')
param alertEmail string

@description('Start date for budget tracking — first day of current month (YYYY-MM-01)')
param startDate string = '2026-04-01'

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: 'budget-investment-coach-demo'
  properties: {
    category: 'Cost'
    amount: monthlyBudgetUsd
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    filter: {
      dimensions: {
        name: 'ResourceGroupName'
        operator: 'In'
        values: [resourceGroup().name]
      }
    }
    notifications: {
      // Alert at 50% — early warning
      alert50Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 50
        contactEmails: [alertEmail]
        thresholdType: 'Actual'
      }
      // Alert at 80% — act now
      alert80Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        contactEmails: [alertEmail]
        thresholdType: 'Actual'
      }
      // Alert at 100% — budget exceeded
      alert100Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        contactEmails: [alertEmail]
        thresholdType: 'Actual'
      }
      // Forecast alert at 110% — will exceed budget this month
      alertForecast110: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 110
        contactEmails: [alertEmail]
        thresholdType: 'Forecasted'
      }
    }
  }
}

output budgetName string = budget.name
