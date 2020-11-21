import logging
import json
import torch
import argparse
from transformers import BertForSequenceClassification
from tweetclassifier.dataset import get_dataloaders
from tweetclassifier.trainer import Trainer
from tweetclassifier.dataset import TweetTransform, parse_json
from tweetclassifier.utils import logging_config, load_object
from tweetclassifier.BertTweetClassifer import BertTweetClassifer

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--train_path",
        type=str,
        required=True,
        help="Path to training data",
    )

    parser.add_argument(
        "--val_path",
        type=str,
        required=True,
        help="Path to training data",
    )

    parser.add_argument(
        "--test_path",
        type=str,
        required=True,
        help="Path to training data",
    )

    parser.add_argument(
        "--max_epochs",
        type=int,
        default=50,
        help="Number of epochs",
    )

    parser.add_argument(
        "--bert_model",
        type=str,
        default="bert-base-uncased",
        help="BERT model",
    )

    parser.add_argument(
        "--log_interval",
        type=int,
        default=10,
        help="Log results every that many timesteps",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size",
    )

    parser.add_argument(
        "--optimizer",
        type=json.loads,
        default='{"fn": "torch.optim.Adam", "kwargs": {"lr": 0.001}}',
        help="Optimizer configurations",
    )

    parser.add_argument(
        "--lr_scheduler",
        type=json.loads,
        default='{"fn": "torch.optim.lr_scheduler.ExponentialLR", "kwargs": {"gamma": 0.9}}',
        help="Learning rate scheduler configurations",
    )

    parser.add_argument(
        "--loss",
        type=json.loads,
        default='{"fn": "torch.nn.BCEWithLogitsLoss", "kwargs": {}}',
        help="Loss function configurations",
    )

    args = parser.parse_args()

    return args


def main(args):
    logging_config()
    datasets, labels = parse_json((args.train_path, args.val_path, args.test_path))
    transform = TweetTransform(args.bert_model, labels)
    train_dataloader, val_dataloader, test_dataloader = get_dataloaders(
        datasets, transform, batch_size=args.batch_size
    )

    model = BertTweetClassifer(args.bert_model, num_labels=len(labels))
    #model = BertForSequenceClassification.from_pretrained(
    #    args.bert_model,
    #    num_labels=len(labels),
    #    output_attentions=False,
    #    output_hidden_states=False,
    #)

    if torch.cuda.is_available():
        model = model.cuda()

    args.optimizer["kwargs"]["params"] = model.parameters()
    optimizer = load_object(args.optimizer["fn"], args.optimizer["kwargs"])

    args.lr_scheduler["kwargs"]["optimizer"] = optimizer
    scheduler = load_object(args.lr_scheduler["fn"], args.lr_scheduler["kwargs"])

    loss = load_object(args.loss["fn"], args.loss["kwargs"])

    trainer = Trainer(
        model=model,
        max_epochs=args.max_epochs,
        optimizer=optimizer,
        scheduler=scheduler,
        loss=loss,
        train_dataloader=train_dataloader,
        val_dataloader=val_dataloader,
        test_dataloader=test_dataloader,
        log_interval=args.log_interval
    )
    trainer.train()
    return


if __name__ == "__main__":
    main(parse_args())
