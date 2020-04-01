#!/usr/bin/eny python
# Kyle Fitzsimmons, 2020
# Serializes Itinerum survey to ODK XForms
import unicodedata
import xml.etree.ElementTree as ET

from itinerum import hardcoded_questions


bind_types = {
    1:   'select1',    # general single-choice
    100: 'select1',    # gender
    101: 'select1',    # age bracket
    103: 'string',     # email
    104: 'select1',    # member_type/occupation
    105: 'geopoint',   # home location
    106: 'geopoint',   # study location
    107: 'geopoint',   # work location
    108: 'select1',    # study - primary mode
    109: 'select1',    # study - secondary mode
    110: 'select1',    # work - primary mode
    111: 'select1',    # work - secondary mode
}


def create_root():
    root = ET.Element('h:html', attrib={'xmlns': 'http://www.w3.org/2002/xforms',
                                        'xmlns:h': 'http://www.w3.org/1999/xhtml',
                                        'xmlns:jr': 'http://openrosa.org/javarosa',
                                        'xmlns:orx': 'http://openrosa.org/xforms',
                                        'xmlns:odk': 'http://www.opendatakit.org/xforms',
                                        'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema'})
    head = ET.SubElement(root, 'h:head')
    title = ET.SubElement(head, 'h:title')
    title.text = 'itinerum'
    model = ET.SubElement(head, 'model')
    ET.SubElement(model, 'instance')
    ET.SubElement(root, 'h:body', attrib={'class': 'pages'})
    return root

def add_xforms_head(root):
    model = root.find('.//model')
    instance = model.find('instance')
    data = ET.SubElement(instance, 'data', attrib={'id': f'Itinerum survey {survey_id}',
                                                   'orxversion': '2014083101'})
    meta = ET.SubElement(data, 'meta')
    ET.SubElement(meta, 'instanceID')

    ET.SubElement(model, 'itext')
    ET.SubElement(model, 'bind', attrib={'nodeset': '/data/meta/instanceID',
                                         'type': 'string',
                                         'readonly': 'true()',
                                         'calculate': "concat('uuid:', uuid())"})


def _add_question_to_toc(root, groups, added_groups, question_type, path_label):
    body = root.find('h:body')

    work_question_types = [107, 110, 111]
    study_question_types = [106, 108, 109]
    if question_type < 100:
        group_label = 'group_dynamic'
    elif 100 <= question_type <= 103:
        group_label = 'group_hardcoded_user'
    elif 104 <= question_type <= 105:
        group_label = 'group_hardcoded_intro'
    elif question_type in work_question_types:
        group_label = 'group_hardcoded_work'
    elif question_type in study_question_types:
        group_label = 'group_hardcoded_study'
    else:
        raise Exception(f'Question type {question_type} has no case.')

    group = groups[group_label]
    ET.SubElement(group, path_label)

    added = False
    if group_label not in added_groups:
        # appears in rcity branch but not odk builder output
        # ET.SubElement(model, 'bind', attrib={'nodeset': f'/data/{group_label}',
        #                                      'required': 'false()'})
        group = ET.SubElement(body, 'group', attrib={'ref': group_label})
        ET.SubElement(group, 'label', attrib={'ref': f"jr:itext('/data/{group_label}:label')"})
        added_groups.append(group_label)
        added = True
    return group_label, added


def _add_question_data(root, group_label, question_label, odk_type, question_choices):
    model = root.find('.//model')
    body = root.find('h:body')

    # get group to append question into
    group = body.find(f"./group[@ref='{group_label}']")
    # determine element type from Itinerum question type
    if odk_type == 'geopoint':
        ET.SubElement(model, 'bind', attrib={'nodeset': f'/data/{group_label}/{question_label}',
                                            'type': 'geopoint',
                                            'required': 'true()'})
        input_ = ET.SubElement(group, 'input', attrib={'ref': f'/data/{group_label}/{question_label}', 
                                                    'appearance': 'maps'})
        ET.SubElement(input_, 'label', attrib={'ref': f"jr:itext('/data/{group_label}/{question_label}:label')"})
    elif odk_type == 'string':
        ET.SubElement(model, 'bind', attrib={'nodeset': f'/data/{group_label}/{question_label}',
                                            'type': 'string',
                                            'required': 'true()'})
        input_ = ET.SubElement(group, 'input', attrib={'ref': f'/data/{group_label}/{question_label}'})
        ET.SubElement(input_, 'label', attrib={'ref': f"jr:itext('/data/{group_label}/{question_label}:label')"})
    elif odk_type == 'select1':
        ET.SubElement(model, 'bind', attrib={'nodeset': f'/data/{group_label}/{question_label}',
                                            'type': 'select1',
                                            'required': 'true()'})
        input_ = ET.SubElement(group, 'select1', attrib={'ref': f'/data/{group_label}/{question_label}'})
        ET.SubElement(input_, 'label', attrib={'ref': f"jr:itext('/data/{group_label}/{question_label}:label')"})
        
        for idx, c in enumerate(question_choices):
            item = ET.SubElement(input_, 'item')
            ET.SubElement(item, 'label', attrib={'ref': f"jr:itext('/data/{group_label}/{question_label}:option{idx}')"})
            item_value = ET.SubElement(item, 'value')
            item_value.text = str(c['choice_num'])

    else:
        raise Exception(f'No case for: {group_label}, {question_label}, {odk_type}')


def add_questions(survey_id, questions, root):
    model = root.find('.//model')
    data = model.find('./instance/data')
    itext = model.find('./itext')

    # create hardcoded and dynamic question groups
    group_labels = [
        'group_hardcoded_intro',
        'group_hardcoded_work',
        'group_hardcoded_study',
        'group_hardcoded_user',
        'group_dynamic'
    ]
    groups = {label: ET.SubElement(data, label) for label in group_labels}

    # itext language tag
    language = None
    if survey_language == 'en':
        language = 'English'
    elif survey_language == 'fr':
        language = 'French'
    translation = ET.SubElement(itext, 'translation', attrib={'lang': language})

    # survey questions
    added_groups = list()
    for q in questions:
        question_label = q['question_label'].lower()
        question_text = q['question_text']
        question_type = q['question_type']
        odk_type = bind_types.get(question_type)
        path_label = (unicodedata.normalize('NFD', question_label)
                                 .encode('ascii', 'ignore')
                                 .decode('utf-8')
                                 .lower())
        group_label, added = _add_question_to_toc(root,
                                                  groups,
                                                  added_groups,
                                                  question_type,
                                                  path_label)

        ## lookup translations for hardcoded questions from file
        # if is_hardcoded_question:
        #     choices_key = 'choices'
        #     if survey_language != 'en':
        #         choices_key = choices_key + f'_{survey_language}'
        #         localized_question = getattr(hardcoded_questions, f'default_questions_{survey_language}')
        #         question_text = localized_question[idx]['prompt']
        
        # add section to itext if not existing
        if added:
            text_ = ET.SubElement(translation, 'text', attrib={'id': f'/data/{group_label}:label'})
            group_value = ET.SubElement(text_, 'value')
            group_value.text = group_label

        # add question text to itext section        
        text = ET.SubElement(translation, 'text', attrib={'id': f'/data/{group_label}/{question_label}:label'})
        question_value = ET.SubElement(text, 'value')
        question_value.text = question_text

        question_choices = q.get('choices', [])
        for idx, c in enumerate(question_choices):
            choice_text = ET.SubElement(translation, 'text', attrib={'id': f'/data/{group_label}/{question_label}:option{idx}'})
            choice_value = ET.SubElement(choice_text, 'value')
            choice_value.text = c['choice_text']

        # add question choice text to itext section
        _add_question_data(root, group_label, question_label, odk_type, question_choices)


def serialize(survey_id, questions):
    root = create_root()
    add_xforms_head(root)
    add_questions(survey_id, questions, root)

    tree = ET.ElementTree(root)
    tree.write('test-form.xml', encoding='utf-8')

    import lxml.etree as etree
    tree = etree.parse('test-form.xml')
    tree.write('test-form-pretty.xml', pretty_print=True)

