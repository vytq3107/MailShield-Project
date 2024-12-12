import pandas as pd
from datasets import DatasetDict, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from transformers import DataCollatorWithPadding
from datasets import load_dataset

# 1. Load the dataset
dataset_dict = load_dataset("zefang-liu/phishing-email-dataset")
print(dataset_dict)

# 2. If the 'test' split is not available, split 'train' into train and validation sets
if 'test' not in dataset_dict:
    dataset_dict = dataset_dict["train"].train_test_split(test_size=0.2)
    # Reorganize the dataset structure into 'train' and 'validation'
    dataset_dict = DatasetDict({
        'train': dataset_dict['train'],
        'validation': dataset_dict['test']
    })

print(dataset_dict)

# 3. Load the pre-trained model and tokenizer
model_path = "google-bert/bert-large-cased"
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 4. Define label mappings
id2label = {0: "Safe Email", 1: "Phishing Email"}
label2id = {"Safe Email": 0, "Phishing Email": 1}

# 5. Load the model with classification-specific parameters
model = AutoModelForSequenceClassification.from_pretrained(
    model_path,
    num_labels=2,
    id2label=id2label,
    label2id=label2id
)

# 6. Freeze the parameters of the base model
for name, param in model.base_model.named_parameters():
    param.requires_grad = False

# 7. Unfreeze the pooling layers of the base model
for name, param in model.base_model.named_parameters():
    if "pooler" in name:
        param.requires_grad = True

# 8. Define the preprocessing function for text
def preprocess_function(examples):
    texts = [str(text) for text in examples["Email Text"]]
    # Convert labels from strings to integers using label2id
    labels = [label2id[label] for label in examples["Email Type"]]
    # Tokenize with padding and truncation
    tokenized_inputs = tokenizer(texts, padding=True, truncation=True, max_length=512)
    tokenized_inputs["labels"] = labels  # Add converted labels
    return tokenized_inputs

# 9. Tokenize the entire dataset
tokenized_data = dataset_dict.map(preprocess_function, batched=True)

# 10. Create a data collator with padding
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 11. Define training hyperparameters
lr = 2e-4
batch_size = 8
num_epochs = 10

training_args = TrainingArguments(
    output_dir="checkpoints",  #Save checkpoints for if error
    learning_rate=lr,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    num_train_epochs=num_epochs,
    logging_strategy="epoch",
    evaluation_strategy="no",  # No evaluation during training
    save_strategy="epoch",  # Save model after every epoch
    load_best_model_at_end=False,  # Do not load the best model since evaluation is skipped
)

# 12. Initialize the Trainer and start training
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_data["train"],
    tokenizer=tokenizer,
    data_collator=data_collator,
)

trainer.train()

# 13. Save the trained model
trainer.save_model("phishing-email-detector-model")  # Save the model to the "final_model" directory

print("Training and model saving completed!")
