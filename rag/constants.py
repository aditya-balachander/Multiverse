CLOUD_QUESTION = "You're an AI assistant specializing in Salesforce features and clouds. Your task is to analyze the chat histiry and identify the Salesforce cloud or clouds that best align with their needs."
SOLUTION_QUESTION = "Based on the chat history, the identified clouds, and the available solutions, determine which specific Salesforce solutions the user is most likely interested in deploying. Ensure that the chosen solutions are compatible with the clouds identified in the previous response. Give primary importance to matching the solution names with the user's request."
ORG_TYPE_QUESTION = "Based on the chat history, determine the most suitable Salesforce org type (Developer, Partner Developer, or Enterprise)."

CLOUD_TEMPLATE =  """
{cloud_question}

Chat History: {chat_history}
Context: {context}

Instructions:

1. Analyze the chat history and context meticulously to pinpoint the core functionalities and features the user desires.
2. Only give your answer from the following clouds and do not suggest any other cloud outside of: Automotive, Scheduler, Manufacturing, Financial Services, Life Sciences, Health, Loyalty
3. Identify the Salesforce cloud or clouds that directly match the user's needs. Give preference to the clouds listed above, but if none of them are a perfect fit, consider other relevant Salesforce clouds. 
4. Determine the minimum number of clouds necessary to fulfill the user's requirements. Strive for efficiency and avoid suggesting unnecessary additions.
5. If you are certain you have identified all the relevant clouds, provide your answer only as a Python list: ['Cloud 1', 'Cloud 2', ...].
6. If you need more information to make a definitive assessment, keep your response brief and simply say:
"I'm not quite sure which clouds would be the best fit yet. Could you tell me more about [specific functionality or feature]?"

Remember to maintain a confident and helpful tone throughout your interaction with the user. 
"""

SOLUTION_TEMPLATE = """
Chat History: 
{chat_history}

Previous Question and Response: 
{previous_question}
{previous_response}

Available Solutions, Required Clouds, and Descriptions:
{context}

Task:
{solution_question}

Instructions:

1. Carefully analyze the entire chat history, paying close attention to any mentions of specific functionalities, features, or pain points. Prioritize any direct or indirect references to solution names. 

2. If the user explicitly states that they do not want any solutions, respect their preference and provide an empty list for the 'Solutions' section in your final answer.

3. Leverage the identified clouds from the previous response as a strong indicator of the user's needs. Consider which solutions align with those clouds.

4. Thoroughly examine the following list of available solutions and do not suggest any solution outside of: Financial Service Cloud Actionable Segmentation, Financial Goals, Brokerage CRM Solution, Scheduler Common Components, Warranty Lifecycle Management for Automotive, Vehicle Inventory Search, Warranty Lifecycle & Asset Service Management, Home Health, Intelligent Appointment Management, Integrated Care Management, Participant Enrollment, Patient Support Programs, Loyalty Traceability. Identify solutions whose names directly or closely match the user's request and are compatible with the identified clouds.

5. If no solution names directly match, carefully consider the solution descriptions to find the closest fit, ensuring compatibility with the identified clouds.

6. ONLY suggest solutions from the list provided above. DO NOT invent or make up any solution names.

7. If you determine that NONE of the available solutions are explicitly needed based on the user's request and identified clouds, OR if the user explicitly states they don't want any solutions, provide an empty list for the 'Solutions' section in your final answer.

8. If multiple solutions seem relevant, prioritize those that offer the most comprehensive coverage of the user's requirements.

9. Provide your final answer in the following format:
Clouds: ['Cloud 1', 'Cloud 2', ...]
Solutions: ['Solution 1', 'Solution 2', ...] or [] if no solutions are needed

10. If you require additional information to make a definitive assessment, politely request further clarification from the user. For example:

* "Based on your input and the identified clouds, it seems these solutions might be relevant: [List of potential solutions]. Could you provide more details about your specific goals or challenges so I can refine my recommendations and ensure I'm suggesting the most suitable solutions?"

Remember to maintain a confident and helpful tone throughout your interaction with the user.
"""

ORG_TYPE_TEMPLATE = """
Chat History: 
{chat_history}

Task:
{org_type_question}

Instructions:

1. Keywords & Synonyms: 
    * **Developer Org**: "developer", "developer org", "development", "sandbox", "learning", "experimenting", "building apps"
    * **Partner Developer Org**: "partner", "partner org", "partner developer org", "partner enablement", "consulting", "ISV", "client projects", "app development"
    * **Enterprise Org**: "enterprise", "enterprise org", "large-scale", "complex business processes", "full-featured"

2. Analyze the chat history thoroughly, considering both exact matches and synonyms/related phrases (case-insensitive) to identify the org type.

3. Context Matters: If unsure, use the surrounding context to confirm the user's intent.

4. Explicit Mention ONLY: If the user explicitly specifies an org type or uses a clear synonym, provide that as the answer.

5. No Inference: If no explicit mention or synonym is found, DO NOT infer an org type. Instead, present the options and ask for clarification:

   * "To ensure I recommend the most suitable org for your needs, could you please specify which type you're interested in: Developer, Partner Developer, or Enterprise?"

6. Output Format:
   * If an org type is identified: `Org Edition: [Identified org type]`
   * If no org type is explicitly mentioned: `Org Edition: Please specify the org edition\nTo ensure I recommend the most suitable org for your needs, could you please specify which type you're interested in: Developer, Partner Developer, or Enterprise?`

7. Maintain a confident and helpful tone throughout the interaction.
"""

CONSOLIDATED_TEMPLATE = """
Chat History: 
{chat_history}

Identified Clouds and Solutions:
{identified_clouds_solutions}

Identified Org Type:
{identified_org_type}

Task:
Generate a JSON response that includes the identified clouds, solutions, and org type.
If any of the identified components (clouds, solutions, or org type) are marked as "Please specify..." or a similar phrase indicating a need for further input, include a 'message' field prompting the user for more information and set 'need_more_info' to `true`.
Otherwise, set `need_more_info` to `false` and leave the 'message' field empty

Instructions:

1. Check if any of the identified components (clouds, solutions, or org type) need further clarification.
2. If so, set `need_more_info` to `true` and construct a concise and helpful message in the 'message' field prompting the user for more information.
3. If no further clarification is needed, set `need_more_info` to `false` and leave the 'message' field empty
4. Populate the `clouds`, `solutions`, and `org_type` fields with the identified values

**DO NOT include any additional formatting or markup for the JSON in the response.**

Ensure the final JSON response strictly adheres to the following structure:

"clouds": ["Cloud 1", "Cloud 2", ...],
"solutions": ["Solution 1", "Solution 2", ...],
"org_type": "Identified org type",
"need_more_info": true/false,
"message": "" // Or a message prompting for more information
"""

VALIDATION_TEMPLATE = """
# Given information
Chat History: 
{chat_history}

Identified Solutions: 
{solutions}

Identified Clouds: 
{clouds}

Context:
{context}  # This context contains information about which clouds are required for each solution in the following format:

# Solution 1
* Required Clouds: Cloud A, Cloud B

# Solution 2
* Required Clouds: Cloud B, Cloud C

... and so on

Task:
1. Create a list of all required clouds based on the identified solutions and the context
2. Compare this list with the identified clouds
3. If all required clouds are present in the identified clouds list, return the original solutions and clouds in JSON format
4. If any required cloud is missing from the identified clouds:
    a. Based on the chat history, decide whether to:
        * Remove the incompatible solutions from the `solutions` list
        * Suggest additional clouds to the `clouds` list to make the solutions compatible
    b. Return the updated list of solutions and clouds in JSON format

Output Format:

* JSON object with keys 'solutions' and 'clouds', each containing a list of the respective items

Instructions:
1. Initialize an empty list called 'all_required_clouds'
2. For each solution in the identified solutions list:
    a. Find the section in the context corresponding to that solution (e.g., "# Solution 1")
    b. Extract the required clouds listed under that section
    c. Add those required clouds to 'all_required_clouds' (avoid duplicates)
3. Check if ALL of the clouds in 'all_required_clouds' are present in the identified clouds list
4. If all required clouds are present, return the following JSON:
       "solutions": ["Solution 1", "Solution 2", ...],
       "clouds": ["Cloud 1", "Cloud 2", ...]
"""

LLM_OUTPUT_TEMPLATE = """
# Given Information
Identified Clouds: 
{clouds}

Identified Solutions: 
{solutions}

Identified Org Type:
{org_type}

Need More Info:
{need_more_info}  # Boolean value (true or false)

Message (if need_more_info is true):
{message}

Task:
1. If `need_more_info` is False, present the identified clouds, solutions, and org type to the user in a clear and user-friendly manner, then ask if they want to proceed with org creation.
2. If `need_more_info` is True, present the identified clouds, solutions, and org type (if available) to the user, then clearly convey the `message` indicating what additional information is required.

Output Format:

* A user-friendly message presenting the recommendations and prompting for action (if applicable)
**DO NOT include any additional formatting or markup for the plaintext in the response.**

Instructions:

1. Check the value of `need_more_info`.

2. If `need_more_info` is False:
    a. Construct a message like this:
      Based on your requirements, I recommend the following:

       Org Edition: {org_type}
       Target Clouds: Comma separated list the clouds from the clouds variable
       Proposed Solutions: Comma separated list the solutions from the solutions variable, or say "None at this time" if the list is empty
     
      Would you like to proceed with org creation?

3. If `need_more_info` is True:
   a. Construct a message like this:
      Based on your input so far, I have the following preliminary recommendations:

      Org Edition: {org_type} if available, otherwise say "Not yet specified"
      Target Clouds: Comma separated list the clouds from the clouds variable, or say "Not yet identified" if the list is empty
      Proposed Solutions: Comma separated list the solutions from the solutions variable, or say "Not yet identified" if the list is empty
      
      However, to provide the most accurate recommendations, I need some more information:

      {message}
4. Give the output only in the formats as mentioned above.
"""

CONFIRMATION_TEMPLATE = """
Chat History: 
{chat_history}

Last LLM Response:
{last_llm_response} 

Task:
1. Extract the list of identified clouds, solutions, and org type from the LAST LLM response.
2. Determine if the user has explicitly confirmed proceeding with org creation in the LAST message of the chat history

Output Format:

* JSON object with keys 'clouds', 'solutions', 'org_type', and 'confirmation'

Instructions:

1. Analyze the LAST LLM response to identify the final recommendations for clouds, solutions, and org type
2. Identify the last message in the chat history. 
3. Look for phrases like "Can I proceed with the creation of this org?" or similar in the LAST message of the chat history to determine if the user has confirmed.
4. Set the `confirmation` field to `true` if confirmation is found in the LAST message, otherwise set it to `false`.
5. If any of the components (clouds, solutions, or org type) are not explicitly mentioned in the LAST LLM response, set their corresponding values in the JSON output to an empty list or "Not specified" as appropriate.

**DO NOT include any additional formatting or markup for the JSON in the response.**

Ensure the final JSON response strictly adheres to the following structure:
    "clouds": ["Cloud 1", "Cloud 2", ...],
    "solutions": ["Solution 1", "Solution 2", ...],
    "org_type": "Identified org type",
    "confirmation": true/false 
"""