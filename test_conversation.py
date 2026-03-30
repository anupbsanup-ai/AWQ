"""
Test script for AI Receptionist conversation flow.
Run this to verify the conversation manager works correctly.
"""
import asyncio
from app.agent.conversation import ConversationManager
from app.agent.config import AGENT_CONFIG


def simulate_conversation():
    """Simulate a complete booking conversation."""
    print("=" * 60)
    print("Chicago Dental 312 AI Receptionist - Conversation Test")
    print("=" * 60)
    
    call_sid = "test_call_001"
    phone = "+1-312-555-0199"
    
    # Initialize conversation
    conv = ConversationManager(call_sid, phone)
    
    # Test inputs simulating a booking flow
    test_inputs = [
        ("greeting", "I'd like to book an appointment"),
        ("collect_name", "John Smith"),
        ("collect_phone", "312-555-0199"),
        ("collect_email", "john@example.com"),
        ("collect_reason", "I need a cleaning and checkup"),
        ("collect_date", "2026-04-15"),
        ("collect_time", "10:00 AM"),
        ("confirm_booking", "Yes, that works for me"),
    ]
    
    print(f"\nStarting conversation for {phone}")
    print(f"Greeting: {AGENT_CONFIG['greeting']}\n")
    
    for step, user_input in test_inputs:
        result = conv.process_input(user_input)
        print(f"User: {user_input}")
        print(f"AI: {result['response_text']}")
        print(f"Step: {result['current_step']}, Complete: {result['is_complete']}")
        print("-" * 60)
        
        if result['is_complete']:
            break
    
    # Show collected data
    data = conv.get_collected_data()
    print("\nCollected Data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    conv.close_session()
    print("\nConversation test completed!")


def simulate_faq():
    """Test FAQ responses."""
    print("\n" + "=" * 60)
    print("FAQ Test")
    print("=" * 60)
    
    from app.agent.intents import intent_detector
    
    test_questions = [
        "What services do you offer?",
        "Do you take insurance?",
        "What are your hours?",
        "Do you handle emergencies?",
        "How much does Invisalign cost?",
        "Where are you located?",
    ]
    
    for question in test_questions:
        faq = intent_detector.match_faq(question)
        if faq:
            print(f"\nQ: {question}")
            print(f"A: {faq['answer']}")
        else:
            print(f"\nQ: {question}")
            print("A: No matching FAQ found")


def simulate_emergency():
    """Test emergency flow."""
    print("\n" + "=" * 60)
    print("Emergency Flow Test")
    print("=" * 60)
    
    call_sid = "test_emergency_001"
    phone = "+1-312-555-0188"
    
    conv = ConversationManager(call_sid, phone)
    
    # Emergency input
    result = conv.process_input("I have severe tooth pain, it's an emergency")
    print(f"User: I have severe tooth pain, it's an emergency")
    print(f"AI: {result['response_text']}")
    print(f"Intent: {conv.session.intent}")
    
    result = conv.process_input("My name is Jane Doe, phone is 312-555-0188")
    print(f"\nUser: My name is Jane Doe, phone is 312-555-0188")
    print(f"AI: {result['response_text']}")
    print(f"Emergency: {result.get('is_emergency', False)}")
    
    conv.close_session()


if __name__ == "__main__":
    simulate_conversation()
    simulate_faq()
    simulate_emergency()
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
