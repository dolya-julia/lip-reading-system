import string

all_symbols = list(string.ascii_lowercase)
symbols = ['_'] + all_symbols + [' '] # blank символ в начале
symbol_to_index = {s: i for i, s in enumerate(symbols)}
index_to_symbol = {i: s for s, i in symbol_to_index.items()}
num_classes = len(symbols)  # Количество классов (включая blank)

print(f"Количество символов в словаре: {num_classes}")

def clean_text(text, allowed_chars):
    """Удаляет из текста все символы, которых нет в словаре"""
    return ''.join([c for c in text if c in allowed_chars])

def text_to_labels(text, symbol_to_index):
    allowed = set(symbol_to_index.keys())
    text = ''.join([c if c in allowed else ' ' for c in text.lower()])
    # заменяем неизвестные символы на пробел, но пробелы НЕ УДАЛЯЕМ
    text = " ".join(text.split())  # нормализуем множественные пробелы
    labels = [symbol_to_index[c] for c in text]
    return labels


import os
import torch
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms


def is_image_file(filename):
    IMG_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp']
    return any(filename.lower().endswith(ext) for ext in IMG_EXTENSIONS)


class LipReadingDataset(Dataset):
    def __init__(self, root_dir, split='train', transform=None, symbol_to_index=None, max_len=168):
        """
        Args:
            root_dir (string): Directory with the dataset.
            split (string): 'train', 'val', or 'test'.
            transform (callable, optional): Optional transform to be applied on a sample.
            symbol_to_index (dict, optional): Mapping from symbol to index.  Required for label processing.
            max_len (int): Maximum sequence length.
        """
        self.root_dir = root_dir
        self.split = split
        self.transform = transform
        self.symbol_to_index = symbol_to_index
        self.max_len = max_len
        self.sequences = []
        self.labels = []

        self.load_data()

    def load_data(self):
        """
        Loads data from the specified split (train, val, test) and populates
        self.sequences and self.labels.  Reads the text labels from the corresponding
        .txt file.
        """
        text_file_path = os.path.join(self.root_dir, f"{self.split}.txt")
        if not os.path.exists(text_file_path):
            raise FileNotFoundError(f"Text file not found: {text_file_path}")

        with open(text_file_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 2:
                print(f"Skipping line due to insufficient data: {line.strip()}")  # Added for debugging
                continue

            relative_path = parts[0]
            text_label = " ".join(parts[1:])  # Объединяем все слова после пути
            full_path = os.path.join(self.root_dir, self.split,
                                     relative_path)  # Path to the *directory* containing frames

            if not os.path.exists(full_path):
                print(f"Warning: Directory not found: {full_path}")
                continue

            image_files = sorted([f for f in os.listdir(full_path) if is_image_file(f)])
            image_paths = [os.path.join(full_path, file) for file in image_files]

            if image_paths:  # Only append if there are images
                self.sequences.append(image_paths)
                self.labels.append(text_label)  # Append the *text* label, not an index yet

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        image_paths = self.sequences[idx]
        orig_len = len(image_paths)
        images = []

        for image_path in image_paths:
            try:
                image = Image.open(image_path).convert('L')
            except FileNotFoundError:
                print(f"Error: Image not found: {image_path}")
                raise  # Re-raise the exception so it's not silently ignored.
            if self.transform:
                image = self.transform(image)
            images.append(image)

        # Padding or truncating sequence
        if len(images) < self.max_len:
            padding_size = self.max_len - len(images)
            padding = [torch.zeros_like(images[0]) for _ in range(padding_size)]
            images.extend(padding)
        elif len(images) > self.max_len:
            images = images[:self.max_len]

        sequence = torch.stack(images)  # Stack images into a single tensor (T, C, H, W)

        # Convert text to labels using the symbol_to_index mapping.
        text = self.labels[idx]
        labels = torch.tensor(text_to_labels(text, self.symbol_to_index), dtype=torch.long)

        return sequence, labels, orig_len

import torch
from torch.nn.utils.rnn import pad_sequence

def collate_fn(batch, padding_value=0):
    """
    Collates batch for CTCLoss, returning:
    - padded_sequences: (B, T, C, H, W)
    - targets: (sum(target_lengths)) - concatenated labels
    - input_lengths: (B) - lengths of input sequences
    - target_lengths: (B) - lengths of target sequences
    """
    sequences, labels, orig_lengths = zip(*batch)

    # Длины меток
    target_lengths = torch.tensor([len(label) for label in labels], dtype=torch.long)

    # Склеиваем метки в один тензор
    targets = torch.cat(labels, dim=0)

    # Stack sequences
    padded_sequences = torch.stack(sequences)

    # Длина входа (предполагаем, что они все одинаковой длины после обработки CNN)
    input_lengths = torch.tensor(
        [min(l, padded_sequences.size(1)) for l in orig_lengths],
        dtype=torch.long
    )

    return padded_sequences, targets, input_lengths, target_lengths

from torch.utils.data import DataLoader
from torchvision import transforms

data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((96, 96)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ]),
    'val': transforms.Compose([
        transforms.Resize((96, 96)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ]),
    'test': transforms.Compose([
        transforms.Resize((96, 96)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])
}

root_dir = "/kaggle/input/lip-reading-dataset/final_dataset"

image_datasets = {
    'train': LipReadingDataset(root_dir, split='train', transform=data_transforms['train'],
                               symbol_to_index=symbol_to_index, max_len=168),
    'val': LipReadingDataset(root_dir, split='val', transform=data_transforms['val'],
                             symbol_to_index=symbol_to_index, max_len=168),
    'test': LipReadingDataset(root_dir, split='test', transform=data_transforms['test'],
                              symbol_to_index=symbol_to_index, max_len=168)
}


# Создаём DataLoader для каждого Dataset
dataloaders = {
    x: DataLoader(
        image_datasets[x],
        batch_size=8,
        shuffle=(x=='train'),  # перемешиваем только для train
        num_workers=4,          # количество параллельных потоков для загрузки
        collate_fn=collate_fn # если используешь CTC
    )
    for x in ['train', 'val', 'test']
}
def labels_to_text(labels, index_to_symbol):
    """
    Преобразует список индексов обратно в строку.
    """
    return ''.join([index_to_symbol[i] for i in labels])

original_text = dataset.labels[0]
encoded = text_to_labels(original_text, symbol_to_index)
decoded = labels_to_text(encoded, {v: k for k, v in symbol_to_index.items()})
print("Оригинальный текст:", original_text)
print("Закодировано:", encoded)
print("Декодировано обратно:", decoded)

import torch
import torch.nn as nn
import torch.nn.functional as F

class LipReading3DCNN(nn.Module):
    def __init__(self, num_classes, lstm_hidden_size=256, lstm_layers=2, dropout=0.2):
        super().__init__()

        # --- 3D CNN ---
        self.conv1 = nn.Conv3d(1, 64, 3, padding=1)
        self.bn1 = nn.BatchNorm3d(64)
        self.pool1 = nn.MaxPool3d((1,2,2))

        self.conv2 = nn.Conv3d(64, 128, 3, padding=1)
        self.bn2 = nn.BatchNorm3d(128)
        self.pool2 = nn.MaxPool3d((2,2,2))

        self.conv3 = nn.Conv3d(128, 256, 3, padding=1)
        self.bn3 = nn.BatchNorm3d(256)
        self.pool3 = nn.MaxPool3d((1,2,2))

        self.dropout3d = nn.Dropout3d(dropout)

        # --- LSTM ---
        # после adaptive pooling H=W=2, C=128
        self.cnn_output_size = 256 * 2 * 2

        self.lstm = nn.LSTM(
            input_size=self.cnn_output_size,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout
        )

        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(lstm_hidden_size*2, num_classes)
        self.log_softmax = nn.LogSoftmax(dim=2)

    def forward(self, x, input_lengths=None):
        # (B, C=1, T, H, W) → (B, T, C, H, W)
        # x = x.permute(0, 2, 1, 3, 4)

        # --- 3D CNN ---
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.dropout3d(x)

        # --- Adaptive pooling по H,W (оставляем T) ---
        T = x.shape[2]
        x = F.adaptive_avg_pool3d(x, (T, 2, 2))  # H=W=2

        B, C, T, H, W = x.shape
        T_out = T

        # --- разворачиваем spatial ---
        x = x.permute(0, 2, 1, 3, 4)   # (B, T, C, H, W)
        x = x.reshape(B, T, C * H * W) # (B, T, features)

        # --- LSTM ---
        lstm_out, _ = self.lstm(x)
        lstm_out = self.dropout(lstm_out)

        # --- классификация ---
        output = self.fc(lstm_out)
        output = self.log_softmax(output)

        return output, T_out

def visualize_predictions(model, val_dataloader, index_to_symbol, device, num_batches=1, num_examples=5):
    model.eval()
    examples_shown = 0
    with torch.no_grad():
        for batch_idx, (data, targets, _, target_lengths) in enumerate(val_dataloader):
            data = data.to(device)
            output, T_out = model(data)
            output = output.transpose(0, 1)  # T', B, C

            batch_size = data.size(0)
            input_lengths = torch.full(
                size=(batch_size,),
                fill_value=T_out,
                dtype=torch.long,
                device=device
            )

            # Декодируем предсказания
            predicted_texts = decode_predictions(output.cpu(), index_to_symbol, input_lengths.cpu())

            # Целевые тексты
            reference_texts = []
            start = 0
            for length in target_lengths:
                reference_text = "".join([index_to_symbol[i.item()] for i in targets[start:start+length]])
                reference_texts.append(reference_text)
                start += length

            # Выбираем случайные примеры из батча
            indices = list(range(batch_size))
            random.shuffle(indices)
            for i in indices:
                print(f"Reference : {reference_texts[i]}")
                print(f"Predicted : {predicted_texts[i]}")
                print("-" * 30)
                examples_shown += 1
                if examples_shown >= num_examples:
                    return

import jiwer
import torch

def decode_predictions(output, index_to_symbol, input_lengths):
    """
    Декодирует выходные данные модели в текст с использованием greedy decoding.

    Args:
        output (torch.Tensor): Выходные данные модели (T, B, C)
        index_to_symbol (dict): Словарь, отображающий индекс символа в символ
        input_lengths (torch.Tensor): Длины входных последовательностей (B)

    Returns:
        list: Список предсказанных текстовых строк
    """
    decoded_texts = []
    for i in range(output.size(1)):  # Iterate over batch
        decoded_text = ""
        last_char = ""
        for t in range(input_lengths[i]):
            best_index = torch.argmax(output[t, i, :]).item()
            char = index_to_symbol[best_index]
            if char != last_char and char != '_':  # Remove duplicates and blanks
                decoded_text += char
            last_char = char
        decoded_texts.append(decoded_text)
    return decoded_texts


def calculate_cer_wer(predicted_texts, reference_texts):
    """
    Вычисляет CER и WER.

    Args:
        predicted_texts (list): Список предсказанных текстовых строк
        reference_texts (list): Список фактических текстовых строк

    Returns:
        tuple: CER и WER
    """
    transformation = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
    ])
    cer = jiwer.cer(reference_texts, predicted_texts)
    wer = jiwer.wer(reference_texts, predicted_texts)
    return cer, wer

def validate(model, val_dataloader, criterion, device, index_to_symbol):
    model.eval()
    total_loss = 0
    all_predicted_texts = []
    all_reference_texts = []

    with torch.no_grad():
        for data, targets, _, target_lengths in val_dataloader:
            data = data.to(device)
            targets = targets.to(device)
            target_lengths = target_lengths.to(device)
            batch_size = data.size(0)

            # --- forward ---
            output, T_out = model(data)  # теперь модель возвращает (output, T_out)
            output = output.transpose(0, 1)  # -> (T', B, num_classes) для CTC

            # Пересчитываем input_lengths для CTC
            input_lengths = torch.full(
                size=(batch_size,),
                fill_value=T_out,
                dtype=torch.long,
                device=device
            )

            # --- loss ---
            loss = criterion(output, targets, input_lengths, target_lengths)
            total_loss += loss.item() * batch_size

            # --- декодирование ---
            predicted_texts = decode_predictions(output.cpu(), index_to_symbol, input_lengths.cpu())

            # Преобразуем индексы в текст
            reference_texts = []
            start = 0
            for length in target_lengths:
                reference_text = "".join([index_to_symbol[i.item()] for i in targets[start:start + length]])
                reference_texts.append(reference_text)
                start += length

            all_predicted_texts.extend(predicted_texts)
            all_reference_texts.extend(reference_texts)

    avg_loss = total_loss / len(val_dataloader.dataset)
    cer, wer = calculate_cer_wer(all_predicted_texts, all_reference_texts)

    return avg_loss, cer, wer


device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = LipReading3DCNN(num_classes).to(device)  # инициализация модели с 3D CNN

# --- Оптимизатор с маленькой скоростью обучения ---
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer,
                max_lr=1e-3,
                epochs=num_epochs,
                steps_per_epoch=len(dataloaders['train']),
                pct_start=0.1,
                div_factor=20,          # стартовый lr=3e-4
                final_div_factor=50     # конечный lr=6e-5
                )

criterion = nn.CTCLoss(blank=0, reduction='mean', zero_infinity=True)
best_val_loss = float('inf')
num_epochs = 100
patience = 7
epochs_no_improve = 0

for epoch in range(num_epochs):
    model.train()
    train_loss = 0.0

    for batch_idx, (data, targets, input_lengths, target_lengths) in enumerate(dataloaders['train']):
        batch_size = data.size(0)

        data = data.to(device)

        # --- Fix input shape ---
        if data.ndim == 4:
            # (B, T, H, W) → (B, 1, T, H, W)
            data = data.unsqueeze(1)

        elif data.ndim == 5 and data.shape[1] not in (1, 3):
            # (B, T, C, H, W) → (B, C, T, H, W)
            data = data.permute(0, 2, 1, 3, 4)

        targets = targets.to(device)
        target_lengths = target_lengths.to(device)

        optimizer.zero_grad(set_to_none=True)

        output, T_out = model(data)  # output: (B, T', num_classes)
        output = output.transpose(0, 1)  # -> (T', B, num_classes) для CTCLoss

        input_lengths = torch.full(
            size=(data.size(0),),
            fill_value=T_out,
            dtype=torch.long,
            device=data.device
        )

        loss = criterion(output, targets, input_lengths, target_lengths)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        if (batch_idx + 1) % 100 == 0:  # вывод каждые 10 батчей
            print(f"[Epoch {epoch + 1}] Batch {batch_idx + 1}/{len(dataloaders['train'])} - Loss: {loss.item():.4f}")

        train_loss += loss.item()

    train_loss /= len(dataloaders['train'])
    val_loss, cer, wer = validate(model, dataloaders['val'], criterion, device, index_to_symbol)
    print(
        f"Эпоха {epoch + 1}/{num_epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, CER: {cer:.4f}, WER: {wer:.4f}")

    # После валидации
    visualize_predictions(model, dataloaders['val'], index_to_symbol, device, num_batches=1)

    # Сохраняем лучшую модель
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), "best_model.pth")
        epochs_no_improve = 0  # сбрасываем счётчик
        print(f"Новая лучшая модель сохранена (Val Loss: {val_loss:.4f})")
    else:
        epochs_no_improve += 1
        print(f"Val loss не улучшился {epochs_no_improve} эпох(и) подряд")

    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'best_val_loss': best_val_loss,
    }, "checkpoint.pth")

    # если несколько эпох подряд без улучшения — останавливаем
    if epochs_no_improve >= patience:
        print(f"Ранняя остановка: нет улучшения {patience} эпох подряд.")
        break