# Colab Deep Learning Script for Safe-Vision AI
# Instructions: 
# 1. Upload this script and synthetic_complaints_sl.csv to Google Colab.
# 2. Run: !pip install transformers torch pandas scikit-learn
# 3. Execute this file.

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, precision_score, recall_score
import time

class ComplaintDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        
        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train_epoch(model, data_loader, optimizer, device):
    model = model.train()
    losses = []
    
    for d in data_loader:
        input_ids = d["input_ids"].to(device)
        attention_mask = d["attention_mask"].to(device)
        labels = d["labels"].to(device)
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        loss = outputs.loss
        losses.append(loss.item())
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        
    return np.mean(losses)

def eval_model(model, data_loader, device):
    model = model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for d in data_loader:
            input_ids = d["input_ids"].to(device)
            attention_mask = d["attention_mask"].to(device)
            labels = d["labels"].to(device)
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            
            _, preds = torch.max(outputs.logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    f1 = f1_score(all_labels, all_preds, average='macro')
    prec = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    rec = recall_score(all_labels, all_preds, average='macro')
    
    return f1, prec, rec

def main():
    print("Loading Data for DistilBERT fine-tuning...")
    df = pd.read_csv("synthetic_complaints_sl.csv")
    
    # Use a small subset if running locally for proof-of-concept
    # For full training on Colab, comment out the following line
    # df = df.sample(500, random_state=42) 
    
    X = df['Description'].values
    y = df['Category'].values
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    num_classes = len(le.classes_)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    
    train_dataset = ComplaintDataset(X_train, y_train, tokenizer)
    test_dataset = ComplaintDataset(X_test, y_test, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=num_classes)
    model = model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    
    epochs = 3
    print("Starting training...")
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs}")
        train_loss = train_epoch(model, train_loader, optimizer, device)
        f1, prec, rec = eval_model(model, test_loader, device)
        print(f"Train Loss: {train_loss:.4f} | Val F1: {f1:.4f} | Val Precision: {prec:.4f} | Val Recall: {rec:.4f}")
        
    print("Saving fine-tuned DistilBERT model...")
    model.save_pretrained('./distilbert_complaint_category')
    tokenizer.save_pretrained('./distilbert_complaint_category')
    
    with open('distilbert_results.txt', 'w') as f:
        f.write(f"DistilBERT Macro F1: {f1:.4f}\n")
        f.write(f"DistilBERT Precision: {prec:.4f}\n")
        f.write(f"DistilBERT Recall: {rec:.4f}\n")
        f.write("Model saved successfully.\n")

if __name__ == "__main__":
    main()
