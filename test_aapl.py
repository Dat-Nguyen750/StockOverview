import requests
import json

def test_aapl_analysis():
    ticker="TSLA"
    """Test AAPL analysis using the running API"""
    
    print(f"🔍 Performing {ticker} stock analysis...")
    print("=" * 50)
    
    try:
        # Test the GET endpoint
        response = requests.get(f"http://localhost:8000/evaluate?ticker={ticker}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 Company: {data['company_name']} ({data['ticker']})")
            print(f"🎯 Composite Score: {data['composite_score']}/100")
            print(f"✅ Verdict: {data['verdict']}")
            print(f"📝 Explanation: {data['explanation']}")
            print()
            
            print("📈 Score Breakdown:")
            for category, score in data['score_breakdown'].items():
                print(f"   • {category.replace('_', ' ').title()}: {score}/100")
            
            print()
            print(f"🕒 Analysis completed at: {data['evaluation_timestamp']}")
            print(f"📚 Data sources: {', '.join(data['data_sources'])}")
            
            # Test POST endpoint with detailed analysis
            print("\n" + "=" * 50)
            print("🔍 Testing detailed analysis...")
            
            post_data = {
                "ticker": ticker,
                "include_detailed_analysis": True
            }
            
            post_response = requests.post(
                "http://localhost:8000/evaluate",
                json=post_data
            )
            
            if post_response.status_code == 200:
                detailed_data = post_response.json()
                print("✅ Detailed analysis successful!")
                
                if 'detailed_analysis' in detailed_data:
                    details = detailed_data['detailed_analysis']
                    print(f"📊 Financial details available: {len(details)} categories")
                    
                    # Show some key financial metrics if available
                    if 'financial_details' in details:
                        fin_details = details['financial_details'].get('details', {})
                        if fin_details:
                            print("\n💰 Key Financial Metrics:")
                            for key, value in fin_details.items():
                                if isinstance(value, (int, float)):
                                    if 'ratio' in key.lower():
                                        print(f"   • {key.replace('_', ' ').title()}: {value:.2f}")
                                    elif 'cagr' in key.lower() or 'margin' in key.lower() or 'roe' in key.lower():
                                        print(f"   • {key.replace('_', ' ').title()}: {value:.1f}%")
                                    else:
                                        print(f"   • {key.replace('_', ' ').title()}: {value:,.0f}")
                                else:
                                    print(f"   • {key.replace('_', ' ').title()}: {value}")
                
                # Print the general summary for POST as well
                if 'general_summary' in detailed_data:
                    print("\n📋 General Summary:")
                    print(detailed_data['general_summary'])
            else:
                print(f"❌ POST request failed: {post_response.status_code}")
                print(post_response.text)
                
        else:
            print(f"❌ GET request failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server")
        print("Make sure the server is running with: python main.py")
    except Exception as e:
        print("Error generating summary:", e)
        general_summary = "Summary unavailable."

if __name__ == "__main__":
    test_aapl_analysis() 