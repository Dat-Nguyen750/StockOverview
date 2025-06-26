import asyncio
import os
from dotenv import load_dotenv
from modules.evaluator import StockEvaluator

# Always load from the correct location, regardless of where you run the script
dotenv_path = os.path.join(os.path.dirname(__file__), "keys.env")
load_dotenv(dotenv_path)

print("FMP_API_KEY loaded:", os.getenv("FMP_API_KEY"))

async def test_evaluator_directly():
    """Test the evaluator directly without going through the API"""
    
    print("🔍 Testing AAPL evaluation directly...")
    print("=" * 50)
    
    try:
        # Initialize the evaluator
        evaluator = StockEvaluator()
        
        # Evaluate AAPL directly
        result = await evaluator.evaluate_company("AAPL")
        
        print(f"✅ Evaluation completed!")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"📊 Company: {result.get('company_name', 'N/A')}")
            print(f"🎯 Composite Score: {result.get('composite_score', 'N/A')}")
            print(f"✅ Verdict: {result.get('verdict', 'N/A')}")
            
            if 'score_breakdown' in result:
                print("\n📈 Score Breakdown:")
                for category, score in result['score_breakdown'].items():
                    print(f"   • {category}: {score}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_evaluator_directly()) 