# Streamlit Property and Tenant Management Application

This application is a Streamlit-based web application designed to manage properties and tenants, track rental payments, and generate reports. It uses SQLite as a database to store property and tenant information, and allows for uploading and managing payment receipts and contracts.

## Features

*   **Property Management**: Add, view, and delete properties.
*   **Tenant Information**: Store and update tenant details, including rental value, start date, guarantee, and deposit amount.
*   **Payment Tracking**: Upload and manage payment receipts (comprobantes) for each property.
*   **Contract Management**: Upload and download tenant contracts.
*   **Reporting**: Generate a PDF report of tenant information.
*   **Data Visualization**: View rental value distribution across properties using an interactive chart.

## Technologies Used

*   **Streamlit**: For building the interactive web interface.
*   **SQLite3**: For the database to store application data.
*   **ReportLab**: For generating PDF reports.
*   **Pandas**: For data manipulation and analysis.
*   **Altair**: For creating interactive data visualizations.
*   **Werkzeug**: For secure filename handling.
*   **Pillow**: For image processing.

## Setup and Installation

To run this application locally, follow these steps:

### 1. Clone the repository (or download the files):

```bash
git clone <repository_url>
cd <repository_name>
```

### 2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: `venv\Scripts\activate`
```

### 3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit application:

```bash
streamlit run app.py
```

This will open the application in your web browser.

## File Structure

```
streamlit_app/
├── app.py
├── database.db  (generated after first run)
├── requirements.txt
└── uploads/     (stores uploaded files like contracts and receipts)
```

## Usage

### Home Page

The home page displays all properties with their current status (Occupied/Available). You can click "Ver Detalles" (View Details) to see more information about a specific property.

### Property Details Page

On the property details page, you can:

*   View existing tenant data.
*   Modify tenant data: Click "Modificar Datos del Inquilino" (Modify Tenant Data) to update rental value, tenant name, start date, guarantee status, deposit amount, and upload a new contract.
*   Upload Payment Receipts: Use the "Subir nuevo comprobante" (Upload new receipt) section to upload PDF or image files for monthly payments. Select the month and year for the payment.
*   View Uploaded Receipts: All uploaded receipts are displayed with a preview and download link.
*   Delete Receipts: You can delete receipts by their ID.

### Reports and Charts

On the home page, you can:

*   Generate a PDF report of all tenant information by clicking "Generar Informe de Inquilinos" (Generate Tenant Report).
*   View a bar chart showing rental values for all properties under "Gráfico de Valores de Renta" (Rental Value Chart).

### Adding and Deleting Properties

*   **Add Property**: Click "Agregar propiedad" (Add Property) on the home page to add a new property to the database.
*   **Delete Property**: Select a property from the dropdown under "Eliminar propiedad" (Delete Property) and click "Eliminar propiedad" to remove it and all associated records and files.

## Database Schema

The application uses an SQLite database with the following tables:

### `propiedades` table

| Column Name          | Type      | Description                                     |
| :------------------- | :-------- | :---------------------------------------------- |
| `id`                 | INTEGER   | Primary Key, Auto-incrementing                  |
| `propiedad_id`       | INTEGER   | Unique ID for the property                      |
| `valor_renta`        | REAL      | Rental value of the property                    |
| `arrendatario`       | TEXT      | Name of the tenant                              |
| `fecha_inicio`       | DATE      | Start date of the rental agreement (YYYY-MM-DD) |
| `garantia`           | INTEGER   | Boolean (0 or 1) indicating if there's a guarantee |
| `monto_deposito`     | REAL      | Deposit amount                                  |
| `comprobante_garantia`| TEXT      | Filename of the guarantee receipt (not used in current code) |
| `comprobante_contrato`| TEXT      | Filename of the contract                        |

### `comprobantes` table

| Column Name          | Type      | Description                                     |
| :------------------- | :-------- | :---------------------------------------------- |
| `id`                 | INTEGER   | Primary Key, Auto-incrementing                  |
| `propiedad_id`       | INTEGER   | Foreign Key referencing `propiedades.propiedad_id` |
| `nombre`             | TEXT      | Filename of the receipt                         |
| `mes`                | TEXT      | Month of the payment (e.g., "Enero")            |
| `anio`               | INTEGER   | Year of the payment                             |

## Contributing

Feel free to fork this repository, open issues, or submit pull requests to improve the application.

## License

This project is open source and available under the MIT License.

## Author

Manus AI


