  ----------------------------------------------------------------------------------------------------------------------------
  Automation Rule  Trigger   Model         Actions/Python Code
  Name                                     
  ---------------- --------- ------------- -----------------------------------------------------------------------------------
  Add conjoint as  On create Appointment   try:
  Contact          and edit  Answer Inputs 

                                           \# Only process if this is a new record

                                           if record and record.create_date == record.write_date:

                                           if record.partner_id:

                                           \# Store spouse details temporarily

                                           spouse_data = {}

                                           \# Check if this is the spouse name question

                                           if record.question_id.display_name == 'Nom du conjoint' and record.value_text_box:

                                           spouse_data\['name'\] = record.value_text_box

                                           \# Check if this is the spouse phone number question

                                           elif record.question_id.display_name == 'Numéro de téléphone du conjoint' and
                                           record.value_text_box:

                                           spouse_data\['phone'\] = record.value_text_box

                                           if spouse_data:

                                           \# Check if a spouse already exists

                                           domain = \[('parent_id', '=', record.partner_id.id)\]

                                           if 'name' in spouse_data:

                                           domain.append(('name', '=', spouse_data\['name'\]))

                                           existing_spouse = env\['res.partner'\].search(domain, limit=1)

                                           if existing_spouse:

                                           \# Update existing spouse record if needed

                                           if 'phone' in spouse_data and existing_spouse.phone != spouse_data\['phone'\]:

                                           existing_spouse.write({'phone': spouse_data\['phone'\]})

                                           

                                           elif 'name' in spouse_data:

                                           \# Create new spouse contact with all available information

                                           create_vals = {

                                           'name': spouse_data\['name'\],

                                           'parent_id': record.partner_id.id,

                                           \#'company_type': 'person', \# \[DELETE LINE\]

                                           'is_company': False

                                           }

                                           if 'phone' in spouse_data:

                                           create_vals\['phone'\] = spouse_data\['phone'\]

                                           spouse = env\['res.partner'\].with_context(

                                           mail_create_nosubscribe=True,

                                           tracking_disable=True

                                           ).create(create_vals)

                                           except Exception as e:

                                           log(f"Add Conjoint as Contact - Error: {str(e)}", level='error')

  Update Contact   On create Appointment   try:
  Info             and edit  Answer Inputs 

                                           \# Only process if this is a new record

                                           if record and record.create_date == record.write_date:

                                           if record.partner_id:

                                           update_values = {}

                                           \# Map questions to partner fields

                                           if record.question_id.display_name == 'Adresse':

                                           update_values\['street'\] = record.value_text_box

                                           elif record.question_id.display_name == 'Code Postale':

                                           update_values\['zip'\] = record.value_text_box

                                           elif record.question_id.display_name == 'Ville':

                                           update_values\['city'\] = record.value_text_box

                                           elif record.question_id.display_name == 'Pays' and record.value_answer_id:

                                           \# For selection field, use value_answer_id instead of value_text_box

                                           country_name = record.value_answer_id.name.strip()

                                           log(f"\[DEBUG\] Pays detected: '{country_name}'", level='info')

                                           country = env\['res.country'\].search(\[('name', '=ilike', country_name)\],
                                           limit=1)

                                           if country:

                                           log(f"\[DEBUG\] Country matched: {country.name} (ID: {country.id})", level='info')

                                           update_values\['country_id'\] = country.id

                                           else:

                                           log(f"\[DEBUG\] No country found for name: '{country_name}'", level='warning')

                                           \# Add phone update if exists

                                           if record.partner_id.phone:

                                           update_values\['phone'\] = record.partner_id.phone

                                           \# Update the contact if we have any values

                                           if update_values:

                                           log(f"\[DEBUG\] Updating partner {record.partner_id.id} with fields:
                                           {list(update_values.keys())}", level='info')

                                           record.partner_id.with_context(mail_create_nosubscribe=True).write(update_values)

                                           except Exception as e:

                                           log(f"Update Contact Info - Error: {str(e)}", level='error')

  Update Calendar  On create Calendar      try:
  Event Organizer  and edit  Event         

                                           user = env.user \# Get the currently connected user

                                           if not user.\_is_public(): \# Only proceed if user is not public

                                           record.write({

                                           'user_id': user.id, \# Set the organizer

                                           'partner_id': user.partner_id.id \# Set the partner associated with the user

                                           })

                                           except Exception as e:

                                           log(f"Update Calendar Event Organizer - Error: {str(e)}", level='error')

  Add Tag on       On create Activity      try:
  Activity         and edit                
  Completion                               

                                           if record.activity_type_id.name == 'Call2' and record.state == 'done':

                                           \# Get or create call2 tag

                                           Call2_tag = env\['calendar.event.type'\].search(\[('name', '=', 'Call2')\],
                                           limit=1)

                                           if not Call2_tag:

                                           Call2_tag = env\['calendar.event.type'\].create({'name': 'Call2'})

                                           \# Add tag to the calendar event

                                           calendar_event = record.calendar_event_id

                                           if calendar_event:

                                           calendar_event.write({'categ_ids': \[(4, Call2_tag.id)\]})

                                           except Exception as e:

                                           log(f"Add Call2 Tag on Activity Completion - Error: ID {record.id}: {str(e)}",
                                           level='error')

  Create activity  On create Calendar      try:
  for NoShow       and edit  Event         

                                           if record.appointment_status == 'no_show':

                                           noshow_activity_type = env\['mail.activity.type'\].search(\[('name', '=',
                                           'NoShow')\], limit=1)

                                           

                                           existing_activity = env\['mail.activity'\].search(\[

                                           ('res_model', '=', 'calendar.event'),

                                           ('res_id', '=', record.id),

                                           ('activity_type_id', '=', noshow_activity_type.id)

                                           \], limit=1)

                                           

                                           \# Get the event organizer, ensuring we don't assign to public user

                                           user = env.user

                                           assigned_user = False

                                           if record.user_id:

                                           assigned_user = record.user_id

                                           elif not user.\_is_public():

                                           assigned_user = user

                                           

                                           if assigned_user:

                                           

                                           activity_values = {

                                           'activity_type_id': noshow_activity_type.id,

                                           'user_id': assigned_user.id,

                                           'res_model_id': env\['ir.model'\].\_get('calendar.event').id,

                                           'res_id': record.id,

                                           'calendar_event_id': record.id,

                                           'date_deadline': datetime.datetime.now().date(),

                                           'summary': f'NoShow: {record.name or "Rendez-vous (Etude)"}',

                                           }

                                           

                                           if existing_activity:

                                           existing_activity.write(activity_values)

                                           else:

                                           env\['mail.activity'\].create(activity_values)

                                           except Exception as e:

                                           log(f"Create Activity for NoShow - Error: ID {record.id}: {str(e)}", level='error')

  Update Calendar  On create Calendar      \# Available variables:
  Status When      and edit  Event         
  Rescheduled                              

                                           \# - env: environment on which the action is triggered

                                           \# - model: model of the record on which the action is triggered; is a void
                                           recordset

                                           \# - record: record on which the action is triggered; may be void

                                           \# - records: recordset of all records on which the action is triggered in
                                           multi-mode; may be void

                                           \# - time, datetime, dateutil, timezone: useful Python libraries

                                           \# - float_compare: utility function to compare floats based on specific precision

                                           \# - b64encode, b64decode: functions to encode/decode binary data

                                           \# - log: log(message, level='info'): logging function to record debug information
                                           in ir.logging table

                                           \# - \_logger: \_logger.info(message): logger to emit messages in server logs

                                           \# - UserError: exception class for raising user-facing warning messages

                                           \# - Command: x2many commands namespace

                                           \# To return an action, assign: action = {...}

  nan              nan       nan           try:

                                           \# Find linked no-show activities

                                           noshow_activities = env\['mail.activity'\].search(\[

                                           ('res_model', '=', 'calendar.event'),

                                           ('res_id', '=', record.id),

                                           ('activity_type_id.name', '=', 'NoShow'),

                                           ('state', '!=', 'done')

                                           \])

                                           

                                           if noshow_activities:

                                           noshow_activities.unlink()

                                           

                                           \# Get OdooBot partner

                                           current_user = env.user.name

                                           odoo_bot_partner = env.ref('base.partner_root')

                                           

                                           \# Add note to calendar event's chatter as OdooBot

                                           record.sudo().message_post(

                                           body=f"NoShow activitée terminée automatiquement suite à la replanification du
                                           rendez-vous par {current_user}",

                                           message_type='comment',

                                           author_id=odoo_bot_partner.id,

                                           subtype_id=env.ref('mail.mt_note').id

                                           )

                                           

                                           except Exception as e:

                                           log(f"Update Calendar Status when Rescheduled - Error: ID {record.id}: {str(e)}",
                                           level='error')

  Update           On create Appointment   try:
  Appointment      and edit  Answer Inputs 
  Title                                    

                                           \# Only process if this is a new record

                                           if record and record.create_date == record.write_date:

                                           if record.partner_id and record.calendar_event_id:

                                           \# Initialize empty list with 5 elements

                                           name_parts = \[''\] \* 5

                                           \# If there's an existing name, try to parse it

                                           current_name = record.calendar_event_id.name or ''

                                           if current_name and '/' in current_name:

                                           current_parts = current_name.split('/')

                                           \# Copy existing parts, up to the length of our target list

                                           for i in range(min(len(current_parts), 5)):

                                           name_parts\[i\] = current_parts\[i\]

                                           

                                           \# Check for SMS confirmation answer

                                           sms_icon = ''

                                           sms_question = env\['appointment.question'\].search(\[

                                           ('display_name', '=', 'Confirmation du rendez-vous par SMS')

                                           \], limit=1)

                                           

                                           if sms_question:

                                           sms_answer = env\['appointment.answer.input'\].search(\[

                                           ('calendar_event_id', '=', record.calendar_event_id.id),

                                           ('question_id', '=', sms_question.id),

                                           ('value_answer_id', '!=', False)

                                           \], limit=1)

                                           

                                           if sms_answer and sms_answer.value_answer_id.name.lower() == 'oui':

                                           sms_icon = '📞'

                                           

                                           \# Update specific part based on the question

                                           if record.question_id.display_name == 'Besoin':

                                           \# Get all answers for the same question (will be one for radio, multiple for
                                           checkbox)

                                           answers = env\['appointment.answer.input'\].search(\[

                                           ('calendar_event_id', '=', record.calendar_event_id.id),

                                           ('question_id', '=', record.question_id.id),

                                           ('value_answer_id', '!=', False)

                                           \])

                                           selected_answers = \[\]

                                           for answer in answers:

                                           if answer.value_answer_id:

                                           selected_answers.append(answer.value_answer_id.name)

                                           name_parts\[3\] = '+'.join(selected_answers) if selected_answers else ''

                                           elif record.question_id.display_name == 'Code Postale':

                                           name_parts\[1\] = record.value_text_box if record.value_text_box else ''

                                           

                                           \# Get other components that don't come from questions

                                           name_parts\[4\] = record.calendar_event_id.user_id.name or name_parts\[4\] \#
                                           Vendeur

                                           name_parts\[0\] = record.partner_id.name or name_parts\[0\] \# Nom Client

                                           name_parts\[2\] = record.partner_id.phone or name_parts\[2\] \# Téléphone

                                           

                                           \# Format the new title, filter out empty strings and add SMS icon if needed

                                           new_title = sms_icon + '/'.join(filter(None, name_parts))

                                           if new_title:

                                           record.calendar_event_id.write({

                                           'name': new_title

                                           })

                                           except Exception as e:

                                           log(f"Update Appointment Title - Error: {str(e)}", level='error')

  Update Project   On create Project       try:
  Folder Name      and edit                

                                           \# Only process if this is a new record (newly created project from template)

                                           if record and record.create_date == record.write_date:

                                           \# Check if project has an associated sale order line

                                           if record.sale_line_id:

                                           \# Get the sales order and client information

                                           sale_order = record.sale_line_id.order_id

                                           customer = sale_order.partner_id

                                           \# Check if we have a documents folder created

                                           if record.documents_folder_id:

                                           \# Create new folder name with SO reference and client name

                                           new_folder_name = f"{sale_order.name} - Projet - {customer.name}"

                                           record.documents_folder_id.write({

                                           'name': new_folder_name

                                           })

                                           

                                           except Exception as e:

                                           log(f"Update Project Folder Name - Error: {str(e)}", level='error')

  Set Welcome Call On create Task          try:
  Deadline         and edit                

                                           \# Only process if this is a new record (newly created task from template)

                                           if record and record.create_date == record.write_date:

                                           \# Check if task name is "Welcom call" (using the exact spelling from your example)

                                           if record.name == "Welcom call":

                                           \# Get the linked sales order from project_sale_order_id

                                           if record.project_sale_order_id:

                                           \# Get the sales order date

                                           order_date = record.project_sale_order_id.date_order

                                           

                                           if order_date:

                                           \# Calculate deadline date (2 days after order date)

                                           deadline_date = order_date + datetime.timedelta(days=2)

                                           

                                           \# Set the deadline to two days after the sales order date

                                           record.write({

                                           'date_deadline': deadline_date

                                           })

                                           

                                           \# Log the action for tracking

                                           log(f"Welcome call deadline set to {deadline_date} (2 days after order date) for
                                           project {record.project_id.name}", level='info')

                                           except Exception as e:

                                           log(f"Set Welcome Call Deadline - Error: {str(e)}", level='error')

  Set Clickable    On create Appointment   try:
  Customer Phone   and edit  Answer Inputs 

                                           \# Only process if this is a new record

                                           if record and record.create_date == record.write_date:

                                           \# We need to make sure the record has a partner_id and a calendar_event_id

                                           if record.partner_id and record.calendar_event_id:

                                           \# Get phone number from partner

                                           partner_phone = record.partner_id.phone

                                           

                                           if partner_phone:

                                           \# Format the phone number for tel: URI

                                           \# Remove any spaces, parentheses, or other non-digit characters except +

                                           clean_phone = ''.join(c for c in partner_phone if c.isdigit() or c =='+')

                                           

                                           \# Create clickable phone number with tel: URI

                                           clickable_phone =
                                           f'`<a href="tel:{clean_phone}">`{=html}{partner_phone}`</a>`{=html}'

                                           

                                           \# Update the customer_tel field on the calendar event

                                           record.calendar_event_id.write({

                                           'x_studio_customer_phone': clickable_phone

                                           })

                                           

                                           \# Log the action for tracking

                                           log(f"Updated customer_tel to clickable link for {partner_phone}", level='info')

                                           except Exception as e:

                                           log(f"Update Customer Phone - Error: {str(e)}", level='error')

  Set Clickable    On create Calendar      try:
  Customer Adress  and edit  Event         

                                           \# Only process if this is a relevant record (new or updated)

                                           if record:

                                           \# We'll need to find all appointment answers for this calendar event

                                           all_answers = env\['appointment.answer.input'\].search(\[

                                           ('calendar_event_id', '=', record.id)

                                           \])

                                           \# Extract address components from answers

                                           street = ''

                                           zip_code = ''

                                           city = ''

                                           country = ''

                                           for answer in all_answers:

                                           if answer.question_id.display_name == 'Adresse' and answer.value_text_box:

                                           street = answer.value_text_box

                                           elif answer.question_id.display_name == 'Code Postale' and answer.value_text_box:

                                           zip_code = answer.value_text_box

                                           elif answer.question_id.display_name == 'Ville' and answer.value_text_box:

                                           city = answer.value_text_box

                                           elif answer.question_id.display_name == 'Pays' and answer.value_answer_id:

                                           \# Get country name from the selection field

                                           country = answer.value_answer_id.name

                                           \# Build full address string if we have enough components

                                           if street or zip_code or city or country:

                                           \# Build formatted address

                                           address_parts = \[\]

                                           if street:

                                           address_parts.append(street)

                                           if zip_code or city:

                                           zip_city = ' '.join(filter(None, \[zip_code, city\]))

                                           if zip_city:

                                           address_parts.append(zip_city)

                                           if country:

                                           address_parts.append(country)

                                           full_address = ','.join(address_parts)

                                           \# Create a Google Maps URL

                                           encoded_address = full_address.replace(' ','+')

                                           maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

                                           \# Create clickable address with HTML

                                           clickable_address =
                                           f'`<a href="{maps_url}" target="_blank">`{=html}{full_address}`</a>`{=html}'

                                           \# Only update if the address has changed

                                           if record.x_studio_customer_address != clickable_address:

                                           \# Update the customer_address field on the calendar event

                                           record.write({

                                           'x_studio_customer_address': clickable_address

                                           })

                                           \# Log the action for tracking

                                           log(f"Updated customer_address to clickable link for {full_address}", level='info')

                                           except Exception as e:

                                           log(f"Update Customer Address - Error: {str(e)}", level='error')

  Set Partner On   On create Appointment   try:
  Behalf           and edit  Answer Inputs 

                                           \# Only process if this is a new record (following your pattern)

                                           if record and record.create_date == record.write_date:

                                           \# Only process if this is the relevant question about "on behalf of partner"

                                           if record.question_id and record.question_id.display_name == 'Rendez-vous pris à la
                                           place de':

                                           \# We need to make sure the record has a calendar_event_id (following your pattern)

                                           if record.calendar_event_id and record.calendar_event_id.appointment_type_id:

                                           \# For dropdown/selection questions, use value_answer_id instead of value_text_box

                                           if record.value_answer_id:

                                           partner_name = record.value_answer_id.name.strip()

                                           if partner_name:

                                           \# Search for the specific category/tag

                                           target_category = env\['res.partner.category'\].search(\[

                                           ('name', '=', 'Call Center') \# Adjust this category name

                                           \], limit=1)

                                           partner = None

                                           if target_category:

                                           \# STRICT: Only exact match with category filter

                                           partner = env\['res.partner'\].search(\[

                                           ('name', '=ilike', partner_name),

                                           ('category_id', 'in', target_category.ids)

                                           \], limit=1)

                                           \# If partner found, update the calendar event

                                           if partner:

                                           \# Only update if the field value has changed

                                           current_partner = record.calendar_event_id.x_studio_rendez_vous_pris_la_place_de

                                           if current_partner != partner:

                                           record.calendar_event_id.write({

                                           'x_studio_rendez_vous_pris_la_place_de': partner.id

                                           })

                                           \# Log the action for tracking (following your logging style)

                                           log(f"Updated 'rendez-vous pris la place de' to partner: {partner.name}",
                                           level='info')

                                           else:

                                           \# Partner not found - log warning

                                           category_name = target_category.name if target_category else 'Category not found'

                                           log(f"Partner not found for name: '{partner_name}' with category:
                                           '{category_name}'", level='warning')

                                           \# If no answer provided, clear the field

                                           else:

                                           if record.calendar_event_id.x_studio_rendez_vous_pris_la_place_de:

                                           record.calendar_event_id.write({

                                           'x_studio_rendez_vous_pris_la_place_de': False

                                           })

                                           log(f"Cleared 'rendez-vous pris la place de' field", level='info')

                                           except Exception as e:

                                           log(f"Set Partner On Behalf - Error: {str(e)}", level='error')

  Subscribe Admins On create Task          \# Available variables:
  to FSM Tasks     and edit                

                                           \# - env: environment on which the action is triggered

                                           \# - model: model of the record on which the action is triggered; is a void
                                           recordset

                                           \# - record: record on which the action is triggered; may be void

                                           \# - records: recordset of all records on which the action is triggered in
                                           multi-mode; may be void

                                           \# - time, datetime, dateutil, timezone: useful Python libraries

                                           \# - float_compare: utility function to compare floats based on specific precision

                                           \# - b64encode, b64decode: functions to encode/decode binary data

                                           \# - log: log(message, level='info'): logging function to record debug information
                                           in ir.logging table

                                           \# - \_logger: \_logger.info(message): logger to emit messages in server logs

                                           \# - UserError: exception class for raising user-facing warning messages

                                           \# - Command: x2many commands namespace

                                           \# To return an action, assign: action = {...}

  Update Clickable On create Calendar      try:
  Address & Phone  and edit  Event         
  from Client                              
  Attendee                                 

                                           if record:

                                           \# Find client attendees: partners not linked to internal users

                                           client_partner = None

                                           for attendee in record.attendee_ids:

                                           partner = attendee.partner_id

                                           if not partner:

                                           continue

                                           \# Check if partner is NOT an internal user

                                           is_internal = any(

                                           user.has_group('base.group_user') for user in partner.user_ids if user.active

                                           )

                                           if not is_internal:

                                           client_partner = partner

                                           break \# Use the first client found

                                           

                                           \# Initialize values

                                           new_address_html = False

                                           new_phone_html = False

                                           

                                           if client_partner:

                                           \# --- Build clickable address ---

                                           addr_parts = \[\]

                                           if client_partner.street:

                                           addr_parts.append(client_partner.street)

                                           if client_partner.street2:

                                           addr_parts.append(client_partner.street2)

                                           city_zip = ' '.join(filter(None, \[client_partner.zip, client_partner.city\]))

                                           if city_zip:

                                           addr_parts.append(city_zip)

                                           if client_partner.country_id:

                                           addr_parts.append(client_partner.country_id.name)

                                           

                                           if addr_parts:

                                           full_addr = ','.join(addr_parts)

                                           encoded_addr = full_addr.replace(' ','+').replace(',','%2C')

                                           maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_addr}"

                                           new_address_html =
                                           f'`<a href="{maps_url}" target="_blank">`{=html}{full_addr}`</a>`{=html}'

                                           

                                           \# --- Build clickable phone ---

                                           phone = client_partner.phone

                                           if phone:

                                           clean_phone = ''.join(c for c in phone if c.isdigit() or c =='+')

                                           if clean_phone:

                                           new_phone_html = f'`<a href="tel:{clean_phone}">`{=html}{phone}`</a>`{=html}'

                                           

                                           \# Prepare updates

                                           update_vals = {}

                                           if new_address_html != record.x_studio_customer_address:

                                           update_vals\['x_studio_customer_address'\] = new_address_html

                                           log(f"Updated customer address to: {new_address_html}", level='info')

                                           

                                           if new_phone_html != record.x_studio_customer_phone:

                                           update_vals\['x_studio_customer_phone'\] = new_phone_html

                                           log(f"Updated customer phone to: {new_phone_html}", level='info')

                                           

                                           \# Apply updates in one write (only if needed)

                                           if update_vals:

                                           record.write(update_vals)

                                           

                                           except Exception as e:

                                           log(f"Client Contact Info Sync Error: {str(e)}", level='error')

  Replace Call     On create Calendar      try:
  Center Emails    and edit  Event         

                                           if record.attendee_ids:

                                           standard_call_center_email = 'rdvcallbgg@gmail.com'

                                           

                                           \# Get all internal users (employees with portal/internal access)

                                           internal_users = env\['res.users'\].search(\[

                                           ('share', '=', False), \# Internal users (not portal users)

                                           ('active', '=', True)

                                           \])

                                           

                                           \# Get all their emails (normalized to lowercase)

                                           internal_user_emails = set()

                                           for user in internal_users:

                                           if user.email:

                                           internal_user_emails.add(user.email.strip().lower())

                                           \# Also check the partner email if different

                                           if user.partner_id and user.partner_id.email:

                                           internal_user_emails.add(user.partner_id.email.strip().lower())

                                           

                                           log(f"Found {len(internal_user_emails)} internal user emails to check",
                                           level='info')

                                           

                                           \# Process each attendee

                                           for attendee in record.attendee_ids:

                                           partner = attendee.partner_id

                                           

                                           if not partner or not partner.email:

                                           continue

                                           

                                           \# Skip if this partner is an internal user themselves (the organizer)

                                           is_internal_user = any(

                                           user.has_group('base.group_user') for user in partner.user_ids if user.active

                                           )

                                           if is_internal_user:

                                           log(f"Skipping internal user partner: {partner.name}", level='info')

                                           continue

                                           

                                           \# This is a CUSTOMER attendee - check their email

                                           customer_email = partner.email.strip().lower()

                                           

                                           \# Skip if already the standard call center email

                                           if customer_email == standard_call_center_email.lower():

                                           log(f"Customer email is already standard: {partner.name}", level='info')

                                           continue

                                           

                                           \# Check if customer email matches any internal user email

                                           if customer_email in internal_user_emails:

                                           \# This is an internal user email, replace it

                                           original_email = partner.email

                                           log(f"Internal user email detected in CUSTOMER: {partner.name} (ID: {partner.id}) -
                                           Email: {original_email}", level='info')

                                           

                                           partner.with_context(

                                           mail_create_nosubscribe=True,

                                           tracking_disable=True

                                           ).write({'email': standard_call_center_email})

                                           

                                           log(f"✓ Replaced internal email '{original_email}' with
                                           '{standard_call_center_email}' for CUSTOMER: {partner.name}", level='info')

                                           else:

                                           \# Real customer email - keep it

                                           log(f"✓ Real customer email kept: {partner.email} for CUSTOMER: {partner.name}",
                                           level='info')

                                           

                                           except Exception as e:

                                           log(f"Replace Internal User Email - Error: {str(e)}", level='error')

  Assign Existing  On create Calendar      try:
  Customer To      and edit  Event         
  Calendar Event                           
  and Opportunity                          

                                           if record:

                                           phone = None

                                           

                                           \# Try to get phone from custom field

                                           try:

                                           if record.x_studio_customer_phone:

                                           phone_text = record.x_studio_customer_phone

                                           if 'tel:' in phone_text:

                                           start = phone_text.find('tel:') + 4

                                           end = phone_text.find('"', start)

                                           if end == -1:

                                           end = phone_text.find('\>', start)

                                           if end \> start:

                                           phone = phone_text\[start:end\]

                                           else:

                                           phone = phone_text\[start:\].strip()

                                           else:

                                           phone = phone_text

                                           except:

                                           pass

                                           

                                           \# Fallback to partner phone

                                           if not phone and record.partner_id:

                                           if record.partner_id.phone:

                                           phone = record.partner_id.phone

                                           

                                           if phone:

                                           \# Clean phone - keep only digits

                                           clean_phone = ''.join(c for c in phone if c.isdigit())

                                           

                                           if len(clean_phone) \>= 8:

                                           last_8\_digits = clean_phone\[-8:\]

                                           log(f"Searching for customer with last 8 digits: {last_8\_digits}", level='info')

                                           

                                           \# Search for existing customers

                                           existing_customers = env\['res.partner'\].search(\[

                                           ('phone', 'ilike', last_8\_digits)

                                           \])

                                           

                                           \# Filter out internal users

                                           real_customers = existing_customers.filtered(

                                           lambda p: not any(user.has_group('base.group_user') for user in p.user_ids if
                                           user.active)

                                           )

                                           

                                           if real_customers:

                                           \# Sort by creation date - oldest first (most likely the real customer)

                                           real_customers = real_customers.sorted(key=lambda p: p.create_date)

                                           customer = real_customers\[0\]

                                           

                                           log(f"Found existing customer: {customer.name} (ID: {customer.id})", level='info')

                                           

                                           \# Find potential duplicates to clean up

                                           \# Duplicates are other partners with the same phone BUT different from the main
                                           customer

                                           potential_duplicates = real_customers.filtered(lambda p: p.id != customer.id)

                                           

                                           \# Also check current attendees for duplicates

                                           attendee_partners = \[att.partner_id for att in record.attendee_ids if
                                           att.partner_id\]

                                           

                                           for attendee_partner in attendee_partners:

                                           \# If this attendee is not the main customer and has similar phone

                                           if attendee_partner.id != customer.id:

                                           \# Check if it's a duplicate (same last 8 digits)

                                           if attendee_partner.phone:

                                           attendee_phone = attendee_partner.phone

                                           attendee_clean = ''.join(c for c in attendee_phone if c.isdigit())

                                           if len(attendee_clean) \>= 8 and attendee_clean\[-8:\] == last_8\_digits:

                                           if attendee_partner not in potential_duplicates:

                                           potential_duplicates

                                           

                                           \# Check if customer is already an attendee

                                           customer_already_attendee = any(

                                           attendee.partner_id.id == customer.id

                                           for attendee in record.attendee_ids

                                           )

                                           

                                           \# Add customer as attendee if not already

                                           if not customer_already_attendee:

                                           record.write({'partner_ids': \[(4, customer.id)\]})

                                           log(f"Added {customer.name} as attendee", level='info')

                                           

                                           \# Update opportunity if exists

                                           try:

                                           if record.opportunity_id:

                                           if record.opportunity_id.partner_id.id != customer.id:

                                           record.opportunity_id.write({'partner_id': customer.id})

                                           log(f"Updated opportunity partner to: {customer.name}", level='info')

                                           except:

                                           pass

                                           

                                           \# Search for related opportunities

                                           opportunities = env\['crm.lead'\].search(\[('calendar_event_ids', 'in',
                                           record.id)\])

                                           for opp in opportunities:

                                           if opp.partner_id.id != customer.id:

                                           opp.write({'partner_id': customer.id})

                                           log(f"Updated opportunity '{opp.name}' to: {customer.name}", level='info')

                                           

                                           \# Clean up duplicates

                                           for duplicate in potential_duplicates:

                                           log(f"Found potential duplicate: {duplicate.name} (ID: {duplicate.id})",
                                           level='info')

                                           

                                           \# Remove from attendees if present

                                           duplicate_attendee = record.attendee_ids.filtered(lambda a: a.partner_id.id ==
                                           duplicate.id)

                                           if duplicate_attendee:

                                           record.write({'partner_ids': \[(3, duplicate.id)\]})

                                           log(f"Removed duplicate {duplicate.name} from attendees", level='info')

                                           

                                           \# Check if safe to delete

                                           other_events = env\['calendar.event'\].search(\[

                                           ('partner_id', '=', duplicate.id),

                                           ('id', '!=', record.id)

                                           \])

                                           

                                           \# Check attendees in other events

                                           other_event_attendees = env\['calendar.attendee'\].search(\[

                                           ('partner_id', '=', duplicate.id),

                                           ('event_id', '!=', record.id)

                                           \])

                                           

                                           other_opps = env\['crm.lead'\].search(\[('partner_id', '=', duplicate.id)\])

                                           

                                           \# Only delete if not used elsewhere

                                           if not other_events and not other_event_attendees and not other_opps:

                                           try:

                                           duplicate_name = duplicate.name

                                           duplicate_id = duplicate.id

                                           duplicate.unlink()

                                           log(f"✓ Deleted duplicate partner: {duplicate_name} (ID: {duplicate_id})",
                                           level='info')

                                           except Exception as delete_error:

                                           log(f"Could not delete duplicate {duplicate.name}: {str(delete_error)}",
                                           level='warning')

                                           else:

                                           log(f"Duplicate {duplicate.name} is used elsewhere, keeping it", level='info')

                                           

                                           log(f"✓ Successfully assigned existing customer: {customer.name}", level='info')

                                           else:

                                           log(f"No existing customer found for: {last_8\_digits}", level='info')

                                           else:

                                           log(f"Phone number too short: {clean_phone}", level='info')

                                           else:

                                           log(f"No phone number found", level='info')

                                           

                                           except Exception as e:

                                           log(f"Find Customer by Phone - Error: {str(e)}", level='error')
  ----------------------------------------------------------------------------------------------------------------------------
