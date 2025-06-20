import csv

with open('data/exports/csv/processing_analytics.csv', 'r') as f:
    reader = csv.DictReader(f)
    costs = []
    api_calls = []
    
    for row in reader:
        if row['total_cost']:
            costs.append(float(row['total_cost']))
        if row['total_api_calls']:
            api_calls.append(int(row['total_api_calls']))
    
total_cost = sum(costs)
total_calls = sum(api_calls)
avg_cost = total_cost / len(costs) if costs else 0
avg_calls = total_calls / len(api_calls) if api_calls else 0

print(f'Current annotation statistics:')
print(f'Total cost for {len(costs)} interviews: ${total_cost:.2f}')
print(f'Total API calls: {total_calls}')
print(f'Average cost per interview: ${avg_cost:.4f}')
print(f'Average API calls per interview: {avg_calls:.1f}')
print(f'Average cost per API call: ${total_cost/total_calls:.6f}')

print(f'\nIf we add moral foundations analysis:')
print(f'Currently have 5 turn-level dimensions')
print(f'Adding 1 more = 20% increase')
print(f'Estimated additional cost: ${total_cost * 0.20:.2f}')
print(f'Total cost would be: ${total_cost * 1.20:.2f}')