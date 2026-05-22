from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

import os
import argparse
import asyncio
import shutil  
import json
from gum import gum
from gum.observers import Screen

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
    
    parser.add_argument('--limit', '-l', type=int, help='Limit the number of results', default=10)
    parser.add_argument('--model', '-m', type=str, help='Core GUM reasoning model to use')
    parser.add_argument('--screen-model', type=str, help='Screenshot vision model to use')
    parser.add_argument(
        '--data-directory',
        type=str,
        help='Directory for GUM data. Defaults to GUM_DATA_DIR or ~/.cache/gum',
    )
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

    data_directory = os.path.expanduser(args.data_directory or os.getenv('GUM_DATA_DIR') or '~/.cache/gum')

    # Handle --reset-cache before anything else
    if getattr(args, 'reset_cache', False):
        cache_dir = data_directory
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

    # you need one of: user_name for listening mode, --query, --recent, or --workflows
    if user_name is None and args.query is None and not getattr(args, 'recent', False) and not getattr(args, 'workflows', False):
        print("Please provide a user name (-u), a query (-q), use --recent, or use --workflows")
        return
    
    if getattr(args, 'workflows', False):
        gum_instance = gum(user_name or os.getenv('USER_NAME') or 'default', model, data_directory=data_directory, enable_batcher=False)
        await gum_instance.connect_db()
        workflows = await gum_instance.recent_workflows(limit=args.limit)
        print(f"\nRecent {len(workflows)} workflows:")
        for w in workflows:
            print(f"\nWorkflow: {w.name}")
            print(f"Input: {w.input}")
            print(f"Output: {w.output}")
            steps = json.loads(w.steps)
            if steps:
                print("Steps:")
                for idx, step in enumerate(steps, 1):
                    confidence = step.get("confidence")
                    suffix = f" (confidence: {confidence})" if confidence is not None else ""
                    print(f"{idx}. {step['step']}{suffix}")
            if w.reasoning:
                print(f"Reasoning: {w.reasoning}")
            if w.confidence is not None:
                print(f"Confidence: {w.confidence:.2f}")
            print(f"Created At: {w.created_at}")
            print("-" * 80)
    elif getattr(args, 'recent', False):
        gum_instance = gum(user_name or os.getenv('USER_NAME') or 'default', model, data_directory=data_directory, enable_batcher=False)
        await gum_instance.connect_db()
        props = await gum_instance.recent(limit=args.limit)
        print(f"\nRecent {len(props)} propositions:")
        for p in props:
            print(f"\nProposition: {p.text}")
            if p.reasoning:
                print(f"Reasoning: {p.reasoning}")
            if p.confidence is not None:
                print(f"Confidence: {p.confidence:.2f}")
            print(f"Created At: {p.created_at}")
            print("-" * 80)
    elif args.query is not None:
        gum_instance = gum(user_name, model, data_directory=data_directory, enable_batcher=False)
        await gum_instance.connect_db()
        result = await gum_instance.query(args.query, limit=args.limit)
        
        # confidences / propositions / number of items returned
        print(f"\nFound {len(result)} results:")
        for prop, score in result:
            print(f"\nProposition: {prop.text}")
            if prop.reasoning:
                print(f"Reasoning: {prop.reasoning}")
            if prop.confidence is not None:
                print(f"Confidence: {prop.confidence:.2f}")
            print(f"Relevance Score: {score:.2f}")
            print("-" * 80)
    else:
        print(f"Listening to {user_name} with model {model} and screen model {screen_model}")
        screenshots_dir = os.path.join(data_directory, 'screenshots')
            
        async with gum(
            user_name, 
            model, 
            Screen(screen_model, screenshots_dir=screenshots_dir),
            data_directory=data_directory,
            min_batch_size=min_batch_size,
            max_batch_size=max_batch_size
        ) as gum_instance:
            await asyncio.Future()  # run forever (Ctrl-C to stop)

def cli():
    asyncio.run(main())

if __name__ == '__main__':
    cli()
