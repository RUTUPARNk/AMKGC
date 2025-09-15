#!/usr/bin/env python3
"""
Performance test script for multiple sessions and long prompts
"""

import asyncio
import time
import random
from typing import List
from backend.services.llm_abstraction import stream_response

# Long prompt (>10k tokens when tokenized)
LONG_PROMPT = """Artificial Intelligence and its Impact on Society

Introduction

Artificial Intelligence (AI) has emerged as one of the most transformative technologies of the 21st century, 
reshaping industries, economies, and daily life in profound ways. From autonomous vehicles navigating city streets 
to virtual assistants managing our schedules, AI systems are becoming increasingly integrated into the fabric of 
modern society. This technological revolution brings with it both tremendous opportunities and significant challenges 
that require careful consideration and proactive management.

The rapid advancement of AI capabilities, particularly in machine learning and deep learning, has enabled computers 
to perform tasks that were once thought to be exclusively within the realm of human intelligence. These include 
image and speech recognition, natural language processing, decision-making, and even creative endeavors such as 
music composition and artistic creation. As AI systems become more sophisticated and ubiquitous, their influence 
on various aspects of society continues to expand, creating a complex landscape of benefits and risks.

Healthcare Revolution

In the healthcare sector, AI is driving a revolution that promises to improve patient outcomes, reduce costs, 
and increase access to medical services. Machine learning algorithms are being used to analyze medical images 
with unprecedented accuracy, often surpassing human radiologists in detecting conditions such as cancer, 
cardiovascular disease, and neurological disorders. AI-powered diagnostic tools can process vast amounts of 
medical data, including patient histories, lab results, and genetic information, to identify patterns and 
make predictions that assist healthcare professionals in making more informed decisions.

Drug discovery, traditionally a time-consuming and expensive process, is being accelerated through AI-driven 
approaches that can analyze molecular structures, predict drug interactions, and identify potential therapeutic 
targets. This has the potential to bring life-saving medications to market faster and at a lower cost. 
Additionally, AI is enabling personalized medicine by tailoring treatments to individual patients based on 
their genetic makeup, lifestyle factors, and medical history.

Robotic surgery systems, guided by AI, are allowing for more precise and minimally invasive procedures, 
reducing recovery times and improving surgical outcomes. Remote monitoring systems powered by AI can track 
patient vital signs and alert healthcare providers to potential issues before they become critical, 
enabling proactive intervention and reducing hospital readmissions.

Educational Transformation

The field of education is experiencing a significant transformation through the integration of AI technologies. 
Personalized learning platforms use AI algorithms to adapt educational content to the individual needs, 
learning styles, and pace of each student. These systems can identify knowledge gaps, provide targeted 
remediation, and offer enrichment opportunities, creating a more effective and engaging learning experience.

Intelligent tutoring systems can provide 24/7 assistance to students, answering questions, providing 
explanations, and offering practice exercises tailored to each learner's level of understanding. 
Natural language processing capabilities enable these systems to understand and respond to student queries 
in a conversational manner, making learning more interactive and accessible.

AI is also being used to automate administrative tasks in educational institutions, such as grading, 
scheduling, and student assessment. This allows educators to focus more time and energy on direct 
instruction and student engagement. Predictive analytics can help identify students who may be at risk 
of falling behind or dropping out, enabling early intervention and support.

Virtual and augmented reality technologies, enhanced by AI, are creating immersive learning environments 
that can transport students to historical events, distant locations, or microscopic worlds, making 
abstract concepts more tangible and memorable. These technologies have particular promise in fields such 
as science, engineering, and medicine, where hands-on experience is crucial but often difficult to provide.

Employment and Economic Disruption

The impact of AI on employment and the economy is one of the most debated aspects of this technological 
revolution. While AI has the potential to create new jobs and industries, it also poses a significant 
threat to existing occupations, particularly those involving routine or predictable tasks. Automation 
technologies powered by AI are increasingly capable of performing jobs in manufacturing, data entry, 
customer service, and even some professional fields such as legal research and financial analysis.

However, the displacement of workers by AI also creates opportunities for job creation in new fields 
related to AI development, deployment, and maintenance. Roles such as AI specialists, data scientists, 
machine learning engineers, and AI ethicists are in high demand and expected to grow significantly 
in the coming years. Additionally, as AI handles more routine tasks, human workers can focus on 
more creative, strategic, and interpersonal activities that require uniquely human skills.

The challenge lies in ensuring that the workforce is prepared for this transition through education 
and retraining programs. Governments, educational institutions, and businesses must collaborate to 
provide opportunities for workers to acquire new skills and adapt to the changing job market. 
This may include initiatives such as lifelong learning programs, apprenticeships, and 
support for entrepreneurship and innovation.

Economic inequality is another concern, as the benefits of AI may not be evenly distributed. 
Companies and individuals with access to AI technologies and the skills to use them effectively 
may see significant gains, while others may be left behind. Policymakers must consider strategies 
to ensure that the economic benefits of AI are shared more broadly, such as through progressive 
taxation, social safety nets, and investments in public infrastructure and services.

Privacy and Surveillance Concerns

The widespread deployment of AI systems has raised significant concerns about privacy and surveillance. 
AI technologies, particularly those involving data collection and analysis, can track and profile 
individuals with unprecedented precision. Smart devices, social media platforms, and online services 
continuously gather data about user behavior, preferences, and interactions, creating detailed 
digital profiles that can be used for targeted advertising, content personalization, and other purposes.

Facial recognition technology, powered by AI, is being deployed in public spaces, airports, 
and other locations, raising questions about the balance between security and privacy. 
While these systems can enhance security and prevent crime, they also have the potential 
to enable mass surveillance and infringe on individual freedoms. The accuracy and bias 
of facial recognition systems, particularly for certain demographic groups, add additional 
concerns about fairness and discrimination.

The collection and analysis of personal data by AI systems also create risks of data breaches 
and misuse. As AI systems become more sophisticated in their ability to infer sensitive 
information from seemingly innocuous data, the potential for privacy violations increases. 
This underscores the need for strong data protection regulations, transparent data practices, 
and robust security measures to safeguard personal information.

Ethical and Governance Challenges

The development and deployment of AI systems raise complex ethical questions that require 
careful consideration and proactive governance. Issues such as algorithmic bias, 
accountability for AI decisions, and the potential for AI to be used for harmful purposes 
are at the forefront of these discussions. AI systems can perpetuate and amplify existing 
biases present in training data, leading to unfair treatment of certain groups in areas 
such as hiring, lending, and criminal justice.

The question of who is responsible when an AI system causes harm is another critical 
ethical challenge. As AI systems become more autonomous and make decisions with 
minimal human oversight, determining accountability becomes more complex. This is 
particularly important in high-stakes applications such as healthcare, transportation, 
and criminal justice, where AI decisions can have life-altering consequences.

The potential for AI to be used for malicious purposes, such as deepfakes, 
automated disinformation campaigns, and cyberattacks, presents additional 
challenges for governance and regulation. Developing effective countermeasures 
and establishing international cooperation to address these threats will 
be crucial for maintaining trust in AI technologies and preventing their misuse.

Future Outlook and Recommendations

As AI continues to evolve and become more integrated into society, it is essential 
to approach its development and deployment with a balanced perspective that 
maximizes benefits while minimizing risks. This requires collaboration between 
technologists, policymakers, ethicists, and other stakeholders to establish 
principles and frameworks for responsible AI development.

Investment in AI research and development should be coupled with 
investments in education and training to ensure that the workforce 
is prepared for the changes ahead. This includes not only technical 
skills related to AI but also critical thinking, creativity, and 
interpersonal skills that will remain valuable in an AI-augmented world.

Regulatory frameworks should be designed to encourage innovation while 
protecting individual rights and societal values. This may involve 
sector-specific regulations for high-risk applications, 
as well as broader principles for AI governance that 
apply across industries and use cases.

International cooperation will be essential for addressing the 
global challenges and opportunities presented by AI. 
This includes sharing best practices, coordinating 
research efforts, and establishing common standards 
for AI safety and ethics.

Conclusion

Artificial Intelligence represents both a tremendous 
opportunity and a significant challenge for modern 
society. Its potential to improve healthcare, 
education, and other aspects of human welfare 
is immense, but so are the risks associated 
with job displacement, privacy violations, 
and ethical concerns. By approaching 
AI development and deployment 
with careful consideration 
of these factors, we can 
work towards a future 
where AI serves to 
enhance human capabilities 
and improve the human 
condition rather than 
replace or diminish 
them.""" * 2  # Duplicate to ensure >10k tokens

async def simulate_session(session_id: int, prompt: str, provider: str = "qwen", model: str = "qwen-72b-chat"):
    """Simulate a single session with a given prompt"""
    print(f"Session {session_id}: Starting with {len(prompt)} characters")
    
    start_time = time.time()
    token_count = 0
    
    try:
        async for token in stream_response(model, prompt, provider):
            token_count += 1
            # Print progress every 50 tokens
            if token_count % 50 == 0:
                elapsed = time.time() - start_time
                rate = token_count / elapsed if elapsed > 0 else 0
                print(f"Session {session_id}: {token_count} tokens, {rate:.2f} tokens/sec")
                
            # Small delay to prevent overwhelming the system
            if token_count % 10 == 0:
                await asyncio.sleep(0.001)
                
    except Exception as e:
        print(f"Session {session_id}: Error - {e}")
        return {"session_id": session_id, "error": str(e)}
    
    end_time = time.time()
    total_time = end_time - start_time
    rate = token_count / total_time if total_time > 0 else 0
    
    print(f"Session {session_id}: Completed - {token_count} tokens in {total_time:.2f}s ({rate:.2f} tokens/sec)")
    
    return {
        "session_id": session_id,
        "token_count": token_count,
        "total_time": total_time,
        "rate": rate
    }

async def run_multiple_sessions(num_sessions: int = 5, prompt: str = LONG_PROMPT):
    """Run multiple concurrent sessions"""
    print(f"Starting {num_sessions} concurrent sessions with long prompt")
    
    # Create tasks for all sessions
    tasks = [
        simulate_session(i, prompt, "qwen", "qwen-72b-chat") 
        for i in range(num_sessions)
    ]
    
    # Run all sessions concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    total_time = end_time - start_time
    print(f"All sessions completed in {total_time:.2f}s")
    
    # Process results
    successful_sessions = [r for r in results if isinstance(r, dict) and "error" not in r]
    failed_sessions = [r for r in results if isinstance(r, dict) and "error" in r]
    
    if successful_sessions:
        avg_tokens = sum(r["token_count"] for r in successful_sessions) / len(successful_sessions)
        avg_rate = sum(r["rate"] for r in successful_sessions) / len(successful_sessions)
        
        print(f"\nPerformance Summary:")
        print(f"  Successful sessions: {len(successful_sessions)}/{num_sessions}")
        print(f"  Failed sessions: {len(failed_sessions)}/{num_sessions}")
        print(f"  Average tokens per session: {avg_tokens:.0f}")
        print(f"  Average rate per session: {avg_rate:.2f} tokens/sec")
        
    return results

async def run_performance_tests():
    """Run comprehensive performance tests"""
    print("Starting Performance Tests")
    print("=" * 50)
    
    # Test 1: Single long prompt
    print("\nTest 1: Single session with long prompt (>10k tokens)")
    result = await simulate_session(1, LONG_PROMPT)
    
    # Wait a bit between tests
    await asyncio.sleep(2)
    
    # Test 2: Multiple concurrent sessions
    print("\nTest 2: Multiple concurrent sessions")
    results = await run_multiple_sessions(3, LONG_PROMPT[:1000])  # Shorter prompt for multiple sessions
    
    print("\nPerformance tests completed.")
    return result, results

if __name__ == "__main__":
    # Run the performance tests
    asyncio.run(run_performance_tests())
