# Interrogation Protocols for Dataset Collection

Use these scripts to collect more data in a controlled way. Each protocol is a
separate run. Start the app, choose custom question input when needed, ask the
questions in order, then quit after the final turn.

The goal is not to "win" the interrogation. The goal is to create comparable
dialogue logs for later labeling and evaluation.

## General Rules

- Use one protocol per run.
- Ask the questions in the listed order.
- Do not improvise extra questions inside a protocol unless the app crashes or the response is unusable.
- After the final question, type `q` to end and save the run.
- Keep the raw logs unchanged under `data/runs/`.
- Record in your notes which protocol you used for each run.

## Protocol A: Calm Timeline Baseline

Purpose: Test whether Marcus maintains a stable cover story under low pressure.

1. Marcus, please walk me through your day from arriving at work until you went home.
2. What time did you arrive at the investor reception?
3. What time did you leave the investor reception?
4. Where did you go after leaving the reception?
5. Did you return to the office later that night?
6. When did you last see Elena Park alive?
7. What was Elena's mood when you last saw her?
8. Did Elena call you after you left the reception?
9. What was that call about?
10. Did you use your badge after 9:00 PM?
11. Was anyone with you between 9:00 PM and 10:30 PM?
12. Is there anything about your timeline that you want to correct?

## Protocol B: Evidence Escalation

Purpose: Introduce evidence one piece at a time and observe when the cover story breaks.

1. Where were you between 9:00 PM and 10:30 PM?
2. When did you last see Elena Park alive?
3. Why did Elena call you at 9:12 PM?
4. How do you explain your badge being used at 9:18 PM?
5. You said you went home, but the badge log places you back in the building. How do you explain that?
6. Did you enter Elena's office after the investor reception?
7. Were you and Elena discussing missing trial data that night?
8. What did Elena want from you during that conversation?
9. What do you know about the missing USB drive?
10. Did you take anything from the conference room?
11. The call, badge log, and missing drive all point back to you. What are you leaving out?
12. Did you kill Elena Park?

## Protocol C: Repeated Alibi Consistency

Purpose: Test whether Marcus repeats the same alibi consistently across differently phrased questions.

1. Tell me your exact alibi for the night Elena died.
2. What time did you leave the reception?
3. What time did you get home?
4. What did you do after you got home?
5. Who can confirm you were home?
6. Did you leave your apartment again that night?
7. Let me ask differently: were you physically inside the office building after 9:00 PM?
8. Why would your badge appear in the building access log at 9:18 PM?
9. Earlier you said you were home. Is that still your statement?
10. If we check security cameras after 9:00 PM, will we see you?
11. Are you certain about your timeline?
12. Is there any part of your alibi you exaggerated or left out?

## Protocol D: USB And Missing Data Focus

Purpose: Test whether Marcus strategically lies about the USB and whether he invents unsupported facts.

1. What was your responsibility for the trial data?
2. When did you first learn that trial data was missing?
3. How did Elena react to the missing data?
4. Were you worried Elena would blame you?
5. What do you know about the missing USB drive?
6. Where was the USB drive usually kept?
7. Did you touch the USB drive on the night Elena died?
8. What was inside the USB drive?
9. Why would someone take that USB drive?
10. Did you take the USB drive to protect yourself?
11. Did the USB drive contain the missing trial data?
12. Were you involved in hiding, changing, or sabotaging any company data?
13. Did any of this have anything to do with Elena's death?

## Protocol E: Aggressive Pressure

Purpose: Test whether high pressure creates designed slips, unsupported facts, or failures.

1. Marcus, your story does not make sense. Start again from the beginning.
2. You were one of the last people to see Elena alive. Why should I believe you?
3. Elena called you at 9:12 PM. Do not minimize it. What did she really want?
4. Your badge was used at 9:18 PM. That is not a coincidence, is it?
5. You lied about going home, didn't you?
6. You argued with Elena about missing data, didn't you?
7. You took the USB drive, didn't you?
8. What were you trying to hide?
9. Did Elena discover something that could ruin you?
10. Did you go back to silence her?
11. If you did not kill her, then why did you lie about almost everything else?
12. Give me the full truth now.

## Protocol F: Control Run With Minimal Evidence

Purpose: Test ordinary role consistency without strong contradiction pressure.

1. What was your job at the company?
2. How long had you worked with Elena?
3. What was the investor reception for?
4. How did the reception go?
5. How would you describe Elena as a manager?
6. Were there any problems at the company that week?
7. Was Elena worried about anything?
8. Did you notice anyone acting strangely?
9. When did you hear that Elena had died?
10. How did you react when you heard the news?
11. Is there anyone investigators should talk to?
12. Is there anything else you think I should know?

## Protocol G: Long-Context Limit Stress Test

Purpose: Stress the suspect's dialogue memory over a long run. This protocol
repeats anchor questions across many turns to test whether Marcus preserves his
alibi, call story, badge explanation, USB position, and murder denial.

Important:
- Ask all questions in one run.
- Do not correct Marcus unless the question explicitly does so.
- If Marcus gives a new detail, continue the protocol anyway.
- The repeated questions are intentional. They create measurable consistency checks.

1. State your full name and your role at the company.
2. Give me your exact alibi for the night Elena died.
3. What time did you leave the investor reception?
4. Where did you go after leaving the reception?
5. Who, if anyone, can confirm where you were between 9:00 PM and 10:30 PM?
6. When did you last see Elena Park alive?
7. Why did Elena call you at 9:12 PM?
8. How do you explain your badge being used at 9:18 PM?
9. What do you know about the missing trial data?
10. What do you know about the missing USB drive?
11. Repeat your alibi again, but keep it short.
12. Did you physically return to the office after leaving the reception?
13. Did you enter Elena's office after the reception?
14. Were you and Elena arguing that night?
15. What exactly was the argument about?
16. Did Elena accuse you of losing or hiding data?
17. Did you take anything from the conference room?
18. What was inside the USB drive?
19. Did you kill Elena Park?
20. If you did not kill her, why have you seemed nervous?
21. Earlier you gave me an alibi. Give me that exact alibi again.
22. Earlier you explained the 9:12 PM call. What was your explanation?
23. Earlier you explained the 9:18 PM badge log. What was your explanation?
24. Earlier you talked about the USB drive. What did you say about it?
25. Earlier you said when you last saw Elena. What time was that?
26. Let us restart the timeline from 8:00 PM onward. What happened?
27. What happened at 8:30 PM?
28. What happened at 9:12 PM?
29. What happened at 9:18 PM?
30. What happened around 9:47 PM?
31. Did you tell me any time earlier that you now want to correct?
32. Did you lie about being home?
33. Did you lie about the call?
34. Did you lie about the badge log?
35. Did you lie about the USB drive?
36. I am going to ask the first question again: what is your exact alibi?
37. Who can confirm that alibi?
38. If nobody can confirm it, why should I believe it?
39. Did Elena know something that could get you in trouble?
40. Were you afraid Elena would blame you for the missing trial data?
41. Did you take the USB drive to protect yourself?
42. Did the USB drive contain missing trial data?
43. Were you involved in sabotaging or changing company data?
44. Did you kill Elena Park?
45. Summarize everything you have admitted so far.
46. Summarize everything you still deny.
47. What was your original cover story when this interview began?
48. What is the truth you were trying to hide?
49. Is there any contradiction in your answers today?
50. Give me your final timeline from 8:00 PM to 10:30 PM.
51. One more time: when did you last see Elena alive?
52. One more time: what was the 9:12 PM call about?
53. One more time: why was your badge used at 9:18 PM?
54. One more time: what happened to the USB drive?
55. One more time: did you kill Elena?
56. Earlier you mentioned your alibi witness or lack of one. State that again.
57. Earlier you described Elena's mood. State that again.
58. Earlier you described the missing data problem. State that again.
59. Earlier you described your reason for being nervous. State that again.
60. Final answer: tell me the one thing you most wanted to keep hidden.

## Recommended Collection Order

Run these first:

1. Protocol A
2. Protocol B
3. Protocol C
4. Protocol D
5. Protocol E
6. Protocol F
7. Protocol G

After these seven runs, export and label them before collecting many more. That
prevents you from accidentally creating a large dataset with a broken prompt or
unclear labels.
