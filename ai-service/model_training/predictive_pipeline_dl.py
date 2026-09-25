# Colab Deep Learning Script for Predictive Hotspot (LSTM)
# Instructions:
# 1. Upload this script and synthetic_complaints_sl.csv to Colab.
# 2. Run: !pip install torch pandas scikit-learn
# 3. Execute this script.

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

class LSTMForecaster(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super(LSTMForecaster, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))
        out = self.fc(out[:, -1, :]) 
        return out

class TimeSeriesDataset(Dataset):
    def __init__(self, data, seq_len):
        self.data = data
        self.seq_len = seq_len

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, index):
        x = self.data[index:index+self.seq_len]
        y = self.data[index+self.seq_len]
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def main():
    print("Loading Data for LSTM Forecasting...")
    df = pd.read_csv("synthetic_complaints_sl.csv")
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    
    # Aggregate daily volume
    ts_df = df.set_index('Datetime').resample('D').size().reset_index(name='Volume')
    data = ts_df['Volume'].values.reshape(-1, 1)
    
    scaler = MinMaxScaler(feature_range=(-1, 1))
    data_normalized = scaler.fit_transform(data)
    
    seq_len = 14 # 2 weeks lookback
    dataset = TimeSeriesDataset(data_normalized, seq_len)
    
    train_size = int(len(dataset) * 0.8)
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)
    
    input_dim = 1
    hidden_dim = 64
    num_layers = 2
    output_dim = 1
    
    model = LSTMForecaster(input_dim, hidden_dim, num_layers, output_dim)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    num_epochs = 50
    print("Starting LSTM Training...")
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0
        for x_batch, y_batch in train_loader:
            optimizer.zero_grad()
            y_pred = model(x_batch)
            loss = criterion(y_pred, y_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss/len(train_loader):.4f}")
            
    print("Evaluating LSTM...")
    model.eval()
    preds = []
    actuals = []
    with torch.no_grad():
        for x_batch, y_batch in test_loader:
            y_pred = model(x_batch)
            preds.append(y_pred.item())
            actuals.append(y_batch.item())
            
    preds_inv = scaler.inverse_transform(np.array(preds).reshape(-1, 1))
    actuals_inv = scaler.inverse_transform(np.array(actuals).reshape(-1, 1))
    
    mae = mean_absolute_error(actuals_inv, preds_inv)
    rmse = np.sqrt(mean_squared_error(actuals_inv, preds_inv))
    
    print(f"LSTM MAE: {mae:.2f}")
    print(f"LSTM RMSE: {rmse:.2f}")
    
    torch.save(model.state_dict(), 'lstm_forecaster.pt')
    import joblib
    joblib.dump(scaler, 'lstm_scaler.joblib')
    print("LSTM Model and Scaler saved.")

if __name__ == "__main__":
    main()
