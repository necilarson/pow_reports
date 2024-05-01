from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Define route for the upload page
@app.route('/')
def upload_file():
    return render_template('upload.html')

# Define route for processing the uploaded file and displaying results
@app.route('/result', methods=['POST'])
def result():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return 'No file uploaded'

    file = request.files['file']

    # Check if the file is empty
    if file.filename == '':
        return 'Empty file'

    # Read the CSV file
    data = pd.read_csv(file)

    # Data processing
    # Replace '0.' with '.'
    data['Product'] = data['Product'].str.replace('0\.', '.')

    # Add new 'Strain' column
    data['Strain'] = data['Product'].apply(lambda x: x.split(' (')[0])

    # Split 'Product Line' and clean ')'
    data[['Device', 'Oil Category']] = data['Product Line'].str.split(' \(', expand=True)
    data['Oil Category'] = data['Oil Category'].str.replace(')', '')

    # Add new 'Weight' column
    data['Weight'] = data['Product'].apply(lambda x: x.rsplit(' ', 1)[1].replace(')', ''))

    # Perform Aggregations
    # Group by 'Strain' and sum the 'Amount Sold (Units)' then sort and print the top 10
    top_10_by_strain = data.groupby('Strain').agg({'Amount Sold (Units)': 'sum'}).nlargest(10, 'Amount Sold (Units)')

    # Group by 'Device' where Oil Category != 'Live Rosin'
    grouped_by_device = data[data['Oil Category'] != 'Live Rosin'].groupby('Device').agg({'Amount Sold (Units)': 'sum'}).sort_values(by='Amount Sold (Units)', ascending=False)

    # Group by 'Oil Category' where Oil Category != 'Live Rosin'
    grouped_by_oil_category = data[data['Oil Category'] != 'Live Rosin'].groupby('Oil Category').agg({'Amount Sold (Units)': 'sum'}).sort_values(by='Amount Sold (Units)', ascending=False)

    # Pivot table Device (exclude Badder) vs Oil Category (exclude Live Rosin)
    pivot_table_device_vs_oil = data[(data['Device'] != 'Badder') & (data['Oil Category'] != 'Live Rosin')].pivot_table(index='Device', columns='Oil Category', values='Amount Sold (Units)', aggfunc='sum', fill_value=0)

    # Group by 'Weight' for 'Oil Category = Live Rosin'
    grouped_by_weight_live_rosin = data[data['Oil Category'] == 'Live Rosin'].groupby('Weight').agg({'Amount Sold (Units)': 'sum'}).sort_values(by='Amount Sold (Units)', ascending=False)

    # Pivot table Live Rosin Strain vs Weight
    pivot_table_live_rosin_strain_vs_weight = data[data['Oil Category'] == 'Live Rosin'].pivot_table(index='Strain', columns='Weight', values='Amount Sold (Units)', aggfunc='sum', fill_value=0)

    # Group by 'Strain' where Device != 'Badder'
    grouped_by_strain = data[data['Device'] != 'Badder'].groupby('Strain').agg({'Amount Sold (Units)': 'sum'}).sort_values(by='Amount Sold (Units)', ascending=False)

    # Convert the plots to base64 encoded strings for embedding in HTML
    plot1 = get_horizontal_bar_chart(top_10_by_strain, 'Top 10 Seller Strains', 'Units Sold', 'Strain')
    plot2 = get_horizontal_bar_chart(grouped_by_device, 'Units Sold Per Device', 'Units Sold', 'Device')
    plot3 = get_horizontal_bar_chart(grouped_by_oil_category, 'Units Sold Per Oil Category', 'Units Sold', 'Oil Category')
    plot4 = get_horizontal_bar_chart(pivot_table_device_vs_oil, 'Units Sold Per Device and Oil Category', 'Units Sold', 'Device')
    plot5 = get_horizontal_bar_chart(grouped_by_weight_live_rosin, 'Badder Units Sold Per Weight', 'Units Sold', 'Weight')
    plot6 = get_horizontal_bar_chart(grouped_by_strain, 'Units Sold Per Strain', 'Units Sold', 'Strain')

    return render_template('result.html', 
                           plot1=plot1, plot2=plot2, plot3=plot3, 
                           plot4=plot4, plot5=plot5, plot6=plot6,
                           grouped_by_device=grouped_by_device,
                           top_10_by_strain=top_10_by_strain,
                           grouped_by_strain=grouped_by_strain,
                           pivot_table_device_vs_oil=pivot_table_device_vs_oil,
                           grouped_by_oil_category=grouped_by_oil_category,
                           pivot_table_live_rosin_strain_vs_weight=pivot_table_live_rosin_strain_vs_weight,
                           grouped_by_weight_live_rosin=grouped_by_weight_live_rosin)

def get_horizontal_bar_chart(data, title, xlabel, ylabel):
    plt.figure(figsize=(10, 10))
    data.plot(kind='barh', color=['#44b314', '#FFA500'])
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)

    # Save plot to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)

    # Encode plot to base64 string
    plot_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return f'data:image/png;base64,{plot_base64}'

if __name__ == '__main__':
    app.run(debug=True)
