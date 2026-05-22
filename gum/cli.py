from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

import os
import argparse
import asyncio
import shutil  
import json
import sys
from gum import gum
from gum.observers import Screen

ACCENT = "\033[96m"
ACCENT_BOLD = "\033[1;96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty() and os.getenv("NO_COLOR") is None


def _style(text: str, *codes: str) -> str:
    if not _supports_color():
        return text
    return "".join(codes) + text + RESET


def _result_header(title: str) -> str:
    rule = "=" * 80
    return f"\n{_style(rule, ACCENT_BOLD)}\n{_style(title, ACCENT_BOLD)}\n{_style(rule, ACCENT_BOLD)}"


def _result_separator() -> str:
    return _style("-" * 80, DIM)


def _label(text: str) -> str:
    return _style(text, BOLD)

class QueryAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            setattr(namespace, self.dest, '')
        else:
            setattr(namespace, self.dest, values)

def parse_args():
    parser = argparse.ArgumentParser(description='GUM - A Python package with command-line interface')
    parser.add_argument('--user-name', '-u', type=str, help='The user name to use')
    
    parser.add_argument(
        '--query', '-q',
        nargs='?',
        action=QueryAction,
        help='Query the GUM with an optional query string',
    )
    parser.add_argument(
        '--recent', '-r',
        action='store_true',
        help='List the most recent propositions instead of running BM25 search',
    )
    parser.add_argument(
        '--workflows', '-w',
        action='store_true',
        help='List the most recent observed workflows',
    )
    parser.add_argument(
        '--merge-workflows',
        action='store_true',
        help='Merge recent fine-grained workflows into canonical workflows',
    )
    
    parser.add_argument('--limit', '-l', type=int, help='Limit the number of results', default=10)
    parser.add_argument('--model', '-m', type=str, help='Core GUM reasoning model to use')
    parser.add_argument('--screen-model', type=str, help='Screenshot vision model to use')
    parser.add_argument('--reset-cache', action='store_true', help='Reset the GUM cache and exit')  # Add this line
    
    # Batching configuration arguments
    parser.add_argument('--min-batch-size', type=int, help='Minimum number of observations to trigger batch processing')
    parser.add_argument('--max-batch-size', type=int, help='Maximum number of observations per batch')

    args = parser.parse_args()

    if not hasattr(args, 'query'):
        args.query = None

    return args

async def main():
    args = parse_args()

    # Handle --reset-cache before anything else
    if getattr(args, 'reset_cache', False):
        cache_dir = os.path.expanduser('~/.cache/gum/')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"Deleted cache directory: {cache_dir}")
        else:
            print(f"Cache directory does not exist: {cache_dir}")
        return

    model = args.model or os.getenv('MODEL_NAME') or 'gpt-4.1-mini'
    screen_model = args.screen_model or os.getenv('SCREEN_MODEL_NAME') or 'gemini-3-pro-preview'
    user_name = args.user_name or os.getenv('USER_NAME')

    # Batching configuration - follow same pattern as other args    
    min_batch_size = args.min_batch_size or int(os.getenv('MIN_BATCH_SIZE', '5'))
    max_batch_size = args.max_batch_size or int(os.getenv('MAX_BATCH_SIZE', '15'))

    # you need one of: user_name for listening mode, --query, --recent, --workflows, or --merge-workflows
    if (
        user_name is None
        and args.query is None
        and not getattr(args, 'recent', False)
        and not getattr(args, 'workflows', False)
        and not getattr(args, 'merge_workflows', False)
    ):
        print("Please provide a user name (-u), a query (-q), use --recent, use --workflows, or use --merge-workflows")
        return
    
    if getattr(args, 'merge_workflows', False):
        gum_instance = gum(user_name or os.getenv('USER_NAME') or 'default', model, enable_batcher=False)
        await gum_instance.connect_db()
        count = await gum_instance.merge_workflows(limit=args.limit)
        print(_result_header("GUM WORKFLOW MERGE"))
        print(f"{_label('Canonical Workflows Created')}: {count}")
    elif getattr(args, 'workflows', False):
        gum_instance = gum(user_name or os.getenv('USER_NAME') or 'default', model, enable_batcher=False)
        await gum_instance.connect_db()
        workflows = await gum_instance.recent_workflows(limit=args.limit)
        print(_result_header(f"GUM WORKFLOWS ({len(workflows)} results)"))
        for w in workflows:
            print(f"\n{_label('Workflow')}: {_style(w.name, ACCENT)}")
            print(f"{_label('Input')}: {w.input}")
            print(f"{_label('Output')}: {w.output}")
            steps = json.loads(w.steps)
            if steps:
                print(f"{_label('Steps')}:")
                for idx, step in enumerate(steps, 1):
                    confidence = step.get("confidence")
                    suffix = f" (confidence: {confidence})" if confidence is not None else ""
                    print(f"{idx}. {step['step']}{suffix}")
            if w.reasoning:
                print(f"{_label('Reasoning')}: {w.reasoning}")
            if w.confidence is not None:
                print(f"{_label('Confidence')}: {w.confidence:.2f}")
            print(f"{_label('Created At')}: {w.created_at}")
            print(_result_separator())
    elif getattr(args, 'recent', False):
        gum_instance = gum(user_name or os.getenv('USER_NAME') or 'default', model, enable_batcher=False)
        await gum_instance.connect_db()
        props = await gum_instance.recent(limit=args.limit)
        print(_result_header(f"GUM PROPOSITIONS ({len(props)} recent results)"))
        for p in props:
            print(f"\n{_label('Proposition')}: {_style(p.text, ACCENT)}")
            if p.reasoning:
                print(f"{_label('Reasoning')}: {p.reasoning}")
            if p.confidence is not None:
                print(f"{_label('Confidence')}: {p.confidence:.2f}")
            print(f"{_label('Created At')}: {p.created_at}")
            print(_result_separator())
    elif args.query is not None:
        gum_instance = gum(user_name, model, enable_batcher=False)
        await gum_instance.connect_db()
        result = await gum_instance.query(args.query, limit=args.limit)
        
        # confidences / propositions / number of items returned
        print(_result_header(f"GUM QUERY RESULTS ({len(result)} matches)"))
        for prop, score in result:
            print(f"\n{_label('Proposition')}: {_style(prop.text, ACCENT)}")
            if prop.reasoning:
                print(f"{_label('Reasoning')}: {prop.reasoning}")
            if prop.confidence is not None:
                print(f"{_label('Confidence')}: {prop.confidence:.2f}")
            print(f"{_label('Relevance Score')}: {score:.2f}")
            print(_result_separator())
    else:
        print(f"Listening to {user_name} with model {model} and screen model {screen_model}")
            
        async with gum(
            user_name, 
            model, 
            Screen(screen_model),
            min_batch_size=min_batch_size,
            max_batch_size=max_batch_size
        ) as gum_instance:
            await asyncio.Future()  # run forever (Ctrl-C to stop)

def cli():
    asyncio.run(main())

if __name__ == '__main__':
    cli()
