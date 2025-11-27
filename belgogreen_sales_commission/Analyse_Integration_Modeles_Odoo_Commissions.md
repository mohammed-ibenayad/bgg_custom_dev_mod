# Analyse d'Intégration - Modèles Odoo pour Système de Commissions Hiérarchiques

**Date:** 26 Novembre 2025  
**Contexte:** Analyse des modèles Odoo existants pour implémenter un système de commissions multi-niveaux

---

## 📋 Table des matières

1. [Modèles Odoo existants](#modèles-odoo-existants)
2. [Analyse des modèles par fonctionnalité](#analyse-des-modèles-par-fonctionnalité)
3. [Gap Analysis détaillée](#gap-analysis-détaillée)
4. [Architecture proposée](#architecture-proposée)
5. [Modèles à créer/étendre](#modèles-à-créer-étendre)
6. [Plan d'implémentation](#plan-dimplémentation)

---

## 1. 📦 Modèles Odoo existants

### Vue d'ensemble
Odoo dispose de **10 modèles** pour gérer les commissions, organisés en 4 catégories :

#### A. Modèles de configuration (3)
| Modèle | Description | Champs clés |
|--------|-------------|-------------|
| `sale.commission.plan` | Plan de commission principal | name, type (target/achievement), periodicity, user_type, state |
| `sale.commission.plan.achievement` | Métrique de performance | type (amount_sold, invoiced, margin, etc.), rate, product |
| `sale.commission.plan.target.commission` | Niveaux de commission | target_completion (%), commission, otc_percentage |

#### B. Modèles de ciblage (2)
| Modèle | Description | Champs clés |
|--------|-------------|-------------|
| `sale.commission.plan.target` | Objectifs de vente | amount, period, date_from, date_to |
| `sale.commission.plan.target.forecast` | Prévisions | forecast, period, user_id |

#### C. Modèles d'affectation (2)
| Modèle | Description | Champs clés |
|--------|-------------|-------------|
| `sale.commission.plan.user` | Attribution plan → utilisateur | plan_id, user_id, date_from, date_to |
| `sale.commission.plan.user.wizard` | Assistant multi-utilisateurs | user_ids |

#### D. Modèles de reporting (3)
| Modèle | Description | Champs clés |
|--------|-------------|-------------|
| `sale.commission.achievement` | Commissions manuelles | amount, user_id, date, type, note |
| `sale.commission.achievement.report` | Rapport réalisations | achieved, plan_id, user_id, period |
| `sale.commission.report` | Rapport commissions | achieved, commission, target_amount, payment_date, forecast |

---

## 2. 🔍 Analyse des modèles par fonctionnalité

### 2.1 Configuration des plans de commission

#### ✅ **Ce qui existe (`sale.commission.plan`)**
```python
Champs principaux:
- name: Nom du plan
- type: 'target' ou 'achievement'
- periodicity: 'monthly', 'quarterly', 'yearly'
- user_type: 'user' ou 'team'
- state: 'draft', 'approved'
- commission_on_target: Montant de commission à 100%
- target_commission: Liste des niveaux (0%, 50%, 100%, 150%...)
- achievement_ids: Métriques de performance
- user_ids: Utilisateurs assignés (via sale.commission.plan.user)
```

#### ❌ **Ce qui manque pour vos besoins**
- **Pas de notion de hiérarchie** (vendeur/chef/directeur)
- **Pas de % différenciés par rôle** pour une même vente
- **Pas de cascade automatique** vers la hiérarchie

---

### 2.2 Calcul des commissions

#### ✅ **Ce qui existe**
- Métriques disponibles via `sale.commission.plan.achievement`:
  - `amount_sold`: Montant des ventes (SO)
  - `amount_invoiced`: Montant facturé
  - `quantity_sold/invoiced`: Quantités
  - `margin`: Marge bénéficiaire
  - `mrr`: Revenus récurrents (si module Subscriptions)

- Calcul automatique basé sur les métriques
- Niveaux progressifs (0%, 50%, 100%, 150%+)

#### ❌ **Ce qui manque**
- **Condition "facture payée"** non prise en compte
- **Calcul simultané multi-niveaux** (vendeur + chef + directeur)
- **Identification automatique de la hiérarchie**

---

### 2.3 Gestion des paiements

#### ⚠️ **Ce qui existe partiellement**
`sale.commission.report` a un champ `payment_date`, mais :
- **Pas de statut** (payé/non payé/en attente)
- **Pas de workflow** de paiement
- **Pas d'encodage manuel** du statut

#### ❌ **Ce qui manque complètement**
- Table des paiements de commissions
- Statut par commission individuelle
- Historique des paiements
- Date de paiement effectif
- Méthode de paiement

---

### 2.4 Interface utilisateur (Wallet)

#### ❌ **Inexistant dans Odoo**
- Aucune vue "Mes commissions" pour les vendeurs
- Aucun dashboard utilisateur
- Aucun système de réclamation
- Aucune notification

---

### 2.5 Reporting et tableaux de bord

#### ✅ **Ce qui existe**
- `sale.commission.report`: Rapport standard avec :
  - achieved, commission, target_amount
  - forecast, payment_date
  - Groupement par user, team, period

- `sale.commission.achievement.report`: Détail des réalisations

#### ❌ **Ce qui manque**
- **Filtres avancés** par statut de paiement
- **Vue hiérarchique** (chef voit son équipe)
- **Recherche par BC/date/vendeur**
- **Tableau récapitulatif admin** pour préparer paiements

---

## 3. 🚨 Gap Analysis détaillée

### Tableau de correspondance Besoins vs Modèles Odoo

| **Besoin fonctionnel** | **Modèle Odoo** | **Couverture** | **Action requise** |
|------------------------|-----------------|----------------|--------------------|
| **1. Configuration hiérarchique** |
| % par rôle (vendeur/chef/directeur) | `sale.commission.plan` | ❌ 0% | **Créer** `hr.commission.role.config` |
| Identification hiérarchie | - | ❌ 0% | **Étendre** `res.users` + `hr.employee` |
| Cascade automatique 3 niveaux | - | ❌ 0% | **Créer** logique calcul |
| **2. Calcul des commissions** |
| Métriques de base | `sale.commission.plan.achievement` | ✅ 100% | Aucune |
| Condition "facture payée" | - | ❌ 0% | **Créer** trigger sur `account.move` |
| Calcul multi-niveaux | `sale.commission.report` | ⚠️ 10% | **Étendre** pour 3 enregistrements/vente |
| **3. Gestion des paiements** |
| Statut paiement | `sale.commission.report.payment_date` | ⚠️ 20% | **Créer** champ `payment_status` |
| Encodage manuel statut | - | ❌ 0% | **Créer** bouton action |
| Historique paiements | - | ❌ 0% | **Créer** `sale.commission.payment` |
| **4. Wallet utilisateur** |
| Vue "Mes commissions" | - | ❌ 0% | **Créer** vue + menu |
| Détail par commission | `sale.commission.report` | ⚠️ 30% | **Créer** vue formulaire détaillée |
| Filtres payé/non payé | - | ❌ 0% | **Créer** filtres search |
| Réclamation paiement | - | ❌ 0% | **Créer** `sale.commission.claim` |
| Notifications | - | ❌ 0% | **Créer** template email |
| **5. Dashboard chef d'équipe** |
| Vue commissions équipe | `sale.commission.report` | ⚠️ 20% | **Créer** domaine filtré |
| Rapport équipe | `sale.commission.achievement.report` | ⚠️ 30% | **Adapter** avec hiérarchie |
| **6. Tableau récapitulatif admin** |
| Vue toutes commissions | `sale.commission.report` | ✅ 60% | **Créer** vue pivot/graph |
| Filtres avancés | - | ⚠️ 30% | **Créer** filtres search |
| Recherche BC/date/vendeur | - | ❌ 0% | **Créer** filtres search |
| Préparation paiements | - | ❌ 0% | **Créer** action batch |
| **7. Ajustements manuels** |
| Modification % par vente | - | ❌ 0% | **Créer** champ override |
| Commissions exceptionnelles | `sale.commission.achievement` | ✅ 80% | **Utiliser** existant |
| Annulation commission | - | ❌ 0% | **Créer** action + historique |
| **8. Sécurité** |
| Droits d'accès | `ir.model.access` | ⚠️ 50% | **Configurer** rules |
| Isolation données | `ir.rule` | ⚠️ 40% | **Créer** record rules |

**Légende:**
- ✅ 80-100%: Utilisable tel quel
- ⚠️ 20-79%: Nécessite adaptation
- ❌ 0-19%: À créer entièrement

---

## 4. 🏗️ Architecture proposée

### 4.1 Relations entre modèles (existants + nouveaux)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONFIGURATION                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  sale.commission.plan (EXISTANT - À ÉTENDRE)                        │
│  ├─ name, type, periodicity                                         │
│  ├─ achievement_ids → sale.commission.plan.achievement              │
│  ├─ target_commission_ids → sale.commission.plan.target.commission  │
│  └─ user_ids → sale.commission.plan.user                            │
│                                                                       │
│  hr.commission.role.config (NOUVEAU)                                 │
│  ├─ role: 'salesperson', 'team_leader', 'sales_director'            │
│  ├─ default_percentage: float                                        │
│  ├─ plan_id → sale.commission.plan                                  │
│  └─ company_id                                                       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      HIÉRARCHIE UTILISATEURS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  res.users (EXISTANT - À ÉTENDRE)                                   │
│  └─ + team_leader_id → res.users                                    │
│     + sales_director_id → res.users                                 │
│     + commission_role: Selection                                     │
│                                                                       │
│  hr.employee (EXISTANT - À ÉTENDRE)                                 │
│  └─ + Même structure hiérarchique                                    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    CALCUL DES COMMISSIONS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  sale.commission (EXISTANT: sale.commission.report - À ÉTENDRE)     │
│  ├─ sale_order_id → sale.order                                      │
│  ├─ invoice_id → account.move                                       │
│  ├─ user_id → res.users (vendeur/chef/directeur)                   │
│  ├─ role: Selection ('salesperson', 'team_leader', 'director')      │
│  ├─ base_amount: Monetary                                           │
│  ├─ commission_percentage: Float                                    │
│  ├─ commission_amount: Monetary (computed)                          │
│  ├─ + payment_status: Selection ('unpaid', 'claimed', 'paid')       │
│  ├─ + payment_date: Date                                            │
│  ├─ + can_be_paid: Boolean (computed: invoice fully paid)           │
│  ├─ + percentage_override: Float (pour ajustements manuels)         │
│  └─ plan_id → sale.commission.plan                                  │
│                                                                       │
│  Triggers:                                                            │
│  - account.move (invoice): when state='posted' AND payment_state='paid'│
│  - Créer 3 enregistrements: vendeur + chef + directeur              │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    GESTION DES PAIEMENTS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  sale.commission.payment (NOUVEAU)                                   │
│  ├─ commission_ids → sale.commission (Many2many)                    │
│  ├─ user_id → res.users                                             │
│  ├─ payment_date: Date                                              │
│  ├─ total_amount: Monetary (computed)                               │
│  ├─ payment_method: Selection                                       │
│  ├─ reference: Char                                                 │
│  ├─ state: Selection ('draft', 'paid', 'cancelled')                │
│  └─ notes: Text                                                     │
│                                                                       │
│  sale.commission.claim (NOUVEAU)                                     │
│  ├─ commission_id → sale.commission                                 │
│  ├─ user_id → res.users (réclamant)                                │
│  ├─ claim_date: Datetime                                            │
│  ├─ state: Selection ('pending', 'approved', 'rejected', 'paid')   │
│  ├─ admin_notes: Text                                               │
│  └─ processed_by → res.users                                        │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    AJUSTEMENTS & EXCEPTIONS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  sale.commission.adjustment (NOUVEAU)                                │
│  ├─ commission_id → sale.commission                                 │
│  ├─ adjustment_type: Selection ('manual_add', 'manual_remove',     │
│  │                              'percentage_override', 'cancellation')│
│  ├─ original_amount: Monetary                                       │
│  ├─ adjusted_amount: Monetary                                       │
│  ├─ reason: Text                                                    │
│  ├─ created_by → res.users                                          │
│  └─ adjustment_date: Datetime                                       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. 🔧 Modèles à créer/étendre

### A. Modèles EXISTANTS à ÉTENDRE

#### 1. `sale.commission.report` → Renommer en `sale.commission`
**Objectif:** Modèle principal des commissions calculées

**Champs à ajouter:**
```python
class SaleCommission(models.Model):
    _name = 'sale.commission'
    _inherit = 'sale.commission.report'  # Hérite des champs existants
    _description = 'Commission'
    
    # NOUVEAUX CHAMPS
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    role = fields.Selection([
        ('salesperson', 'Vendeur'),
        ('team_leader', 'Chef d\'équipe'),
        ('sales_director', 'Directeur Commercial')
    ], string='Rôle', required=True)
    
    payment_status = fields.Selection([
        ('unpaid', 'Non payé'),
        ('claimed', 'Réclamé'),
        ('processing', 'En traitement'),
        ('paid', 'Payé')
    ], string='Statut paiement', default='unpaid', tracking=True)
    
    payment_date = fields.Date(string='Date de paiement')
    payment_id = fields.Many2one('sale.commission.payment', string='Paiement')
    
    can_be_paid = fields.Boolean(
        string='Peut être payé',
        compute='_compute_can_be_paid',
        store=True
    )
    
    percentage_override = fields.Float(
        string='% Commission (manuel)',
        help='Laisser vide pour utiliser le % par défaut'
    )
    
    actual_percentage = fields.Float(
        string='% Commission effectif',
        compute='_compute_actual_percentage',
        store=True
    )
    
    notes = fields.Text(string='Notes')
    is_adjustment = fields.Boolean(string='Est un ajustement', default=False)
    
    @api.depends('invoice_id.payment_state')
    def _compute_can_be_paid(self):
        for rec in self:
            rec.can_be_paid = (
                rec.invoice_id.payment_state == 'paid' and
                rec.payment_status == 'unpaid'
            )
    
    @api.depends('percentage_override', 'plan_id', 'role')
    def _compute_actual_percentage(self):
        for rec in self:
            if rec.percentage_override:
                rec.actual_percentage = rec.percentage_override
            else:
                # Chercher le % par défaut pour ce rôle dans le plan
                config = self.env['hr.commission.role.config'].search([
                    ('plan_id', '=', rec.plan_id.id),
                    ('role', '=', rec.role)
                ], limit=1)
                rec.actual_percentage = config.default_percentage if config else 0.0
```

**Relations:**
- Garde toutes les relations existantes de `sale.commission.report`
- Ajoute liens vers SO, Invoice, Paiement

---

#### 2. `sale.commission.plan`
**Objectif:** Ajouter configuration hiérarchique

**Champs à ajouter:**
```python
class SaleCommissionPlan(models.Model):
    _inherit = 'sale.commission.plan'
    
    # NOUVEAUX CHAMPS
    is_hierarchical = fields.Boolean(
        string='Plan hiérarchique',
        default=False,
        help='Si activé, calcule commissions pour vendeur + chef + directeur'
    )
    
    role_config_ids = fields.One2many(
        'hr.commission.role.config',
        'plan_id',
        string='Configuration par rôle'
    )
    
    require_invoice_paid = fields.Boolean(
        string='Facture payée requise',
        default=True,
        help='Ne calculer commissions que si facture totalement payée'
    )
```

---

#### 3. `res.users` et `hr.employee`
**Objectif:** Ajouter hiérarchie commerciale

**Champs à ajouter:**
```python
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # NOUVEAUX CHAMPS
    commission_role = fields.Selection([
        ('salesperson', 'Vendeur'),
        ('team_leader', 'Chef d\'équipe'),
        ('sales_director', 'Directeur Commercial')
    ], string='Rôle commission')
    
    team_leader_id = fields.Many2one(
        'res.users',
        string='Chef d\'équipe',
        domain=[('commission_role', '=', 'team_leader')]
    )
    
    sales_director_id = fields.Many2one(
        'res.users',
        string='Directeur commercial',
        domain=[('commission_role', '=', 'sales_director')]
    )
    
    team_member_ids = fields.One2many(
        'res.users',
        'team_leader_id',
        string='Membres de l\'équipe'
    )
    
    my_commission_ids = fields.One2many(
        'sale.commission',
        'user_id',
        string='Mes commissions'
    )
    
    commission_count = fields.Integer(
        compute='_compute_commission_count'
    )
    
    commission_unpaid_total = fields.Monetary(
        compute='_compute_commission_totals',
        string='Commissions non payées'
    )
    
    commission_paid_total = fields.Monetary(
        compute='_compute_commission_totals',
        string='Commissions payées'
    )
```

---

### B. Modèles NOUVEAUX à CRÉER

#### 1. `hr.commission.role.config`
**Objectif:** Configuration % par rôle dans un plan

```python
class HrCommissionRoleConfig(models.Model):
    _name = 'hr.commission.role.config'
    _description = 'Configuration commission par rôle'
    
    plan_id = fields.Many2one(
        'sale.commission.plan',
        string='Plan de commission',
        required=True,
        ondelete='cascade'
    )
    
    role = fields.Selection([
        ('salesperson', 'Vendeur'),
        ('team_leader', 'Chef d\'équipe'),
        ('sales_director', 'Directeur Commercial')
    ], string='Rôle', required=True)
    
    default_percentage = fields.Float(
        string='Pourcentage par défaut',
        required=True,
        digits=(5, 2)
    )
    
    company_id = fields.Many2one(
        'res.company',
        related='plan_id.company_id',
        store=True
    )
    
    _sql_constraints = [
        ('unique_plan_role', 'unique(plan_id, role)',
         'Un seul % par rôle et par plan!')
    ]
```

---

#### 2. `sale.commission.payment`
**Objectif:** Enregistrer les paiements groupés

```python
class SaleCommissionPayment(models.Model):
    _name = 'sale.commission.payment'
    _description = 'Paiement de commissions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    commission_ids = fields.Many2many(
        'sale.commission',
        string='Commissions',
        domain=[('payment_status', 'in', ['unpaid', 'claimed'])]
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Bénéficiaire',
        required=True
    )
    
    payment_date = fields.Date(
        string='Date de paiement',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    
    total_amount = fields.Monetary(
        string='Montant total',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    payment_method = fields.Selection([
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('cash', 'Espèces'),
        ('other', 'Autre')
    ], string='Méthode de paiement', required=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('paid', 'Payé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('commission_ids.commission_amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.commission_ids.mapped('commission_amount'))
    
    def action_confirm(self):
        self.state = 'confirmed'
    
    def action_mark_paid(self):
        self.state = 'paid'
        self.commission_ids.write({
            'payment_status': 'paid',
            'payment_date': self.payment_date,
            'payment_id': self.id
        })
```

---

#### 3. `sale.commission.claim`
**Objectif:** Réclamations de paiement par les vendeurs

```python
class SaleCommissionClaim(models.Model):
    _name = 'sale.commission.claim'
    _description = 'Réclamation de commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    commission_ids = fields.Many2many(
        'sale.commission',
        string='Commissions réclamées'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Réclamant',
        required=True,
        default=lambda self: self.env.user
    )
    
    claim_date = fields.Datetime(
        string='Date de réclamation',
        required=True,
        default=fields.Datetime.now
    )
    
    total_amount = fields.Monetary(
        string='Montant total',
        compute='_compute_total_amount',
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    state = fields.Selection([
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('paid', 'Payé')
    ], string='État', default='pending', tracking=True)
    
    notes = fields.Text(string='Commentaire du vendeur')
    admin_notes = fields.Text(string='Notes admin')
    
    processed_by = fields.Many2one(
        'res.users',
        string='Traité par'
    )
    
    processed_date = fields.Datetime(string='Date de traitement')
    
    @api.depends('commission_ids.commission_amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.commission_ids.mapped('commission_amount'))
    
    def action_approve(self):
        self.state = 'approved'
        self.processed_by = self.env.user
        self.processed_date = fields.Datetime.now()
        self.commission_ids.write({'payment_status': 'processing'})
        # Notification vendeur
        
    def action_reject(self):
        self.state = 'rejected'
        self.processed_by = self.env.user
        self.processed_date = fields.Datetime.now()
        # Notification vendeur
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'sale.commission.claim'
            ) or _('New')
        result = super().create(vals)
        # Notification aux admins
        result._notify_admins()
        return result
    
    def _notify_admins(self):
        """Notifier les admins via email/activité"""
        admin_group = self.env.ref('sales_team.group_sale_manager')
        admins = self.env['res.users'].search([
            ('groups_id', 'in', admin_group.ids)
        ])
        # Créer activité pour chaque admin
        for admin in admins:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=admin.id,
                summary=f'Nouvelle réclamation: {self.name}'
            )
```

---

#### 4. `sale.commission.adjustment`
**Objectif:** Historique des ajustements manuels

```python
class SaleCommissionAdjustment(models.Model):
    _name = 'sale.commission.adjustment'
    _description = 'Ajustement de commission'
    _inherit = ['mail.thread']
    
    commission_id = fields.Many2one(
        'sale.commission',
        string='Commission',
        required=True
    )
    
    adjustment_type = fields.Selection([
        ('percentage_override', 'Modification du %'),
        ('manual_add', 'Ajout manuel'),
        ('manual_remove', 'Retrait manuel'),
        ('cancellation', 'Annulation (vente annulée)')
    ], string='Type', required=True)
    
    original_amount = fields.Monetary(
        string='Montant original',
        currency_field='currency_id'
    )
    
    adjusted_amount = fields.Monetary(
        string='Montant ajusté',
        currency_field='currency_id'
    )
    
    difference = fields.Monetary(
        string='Différence',
        compute='_compute_difference',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='commission_id.currency_id'
    )
    
    reason = fields.Text(string='Raison', required=True)
    
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    adjustment_date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    @api.depends('original_amount', 'adjusted_amount')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.adjusted_amount - rec.original_amount
```

---

## 6. 📅 Plan d'implémentation

### Phase 1: Fondations (Semaine 1-2) - 8 jours
**Objectif:** Mettre en place la structure de base

#### Jour 1-2: Configuration hiérarchique
- [ ] Créer modèle `hr.commission.role.config`
- [ ] Étendre `sale.commission.plan` avec champs hiérarchiques
- [ ] Étendre `res.users` avec hiérarchie (team_leader_id, etc.)
- [ ] Créer vues formulaire/liste pour configuration rôles

#### Jour 3-4: Extension du modèle commission
- [ ] Étendre `sale.commission.report` → `sale.commission`
- [ ] Ajouter champs: payment_status, role, percentage_override
- [ ] Créer méthodes compute: can_be_paid, actual_percentage
- [ ] Tests unitaires

#### Jour 5-6: Logique de calcul hiérarchique
- [ ] Créer méthode `_create_hierarchical_commissions()`
- [ ] Trigger sur `account.move` (facture payée)
- [ ] Identifier vendeur → chef → directeur automatiquement
- [ ] Créer 3 enregistrements avec % respectifs
- [ ] Tests calcul

#### Jour 7-8: Modèle de paiement
- [ ] Créer `sale.commission.payment`
- [ ] Vues formulaire/liste/kanban
- [ ] Actions: confirmer, marquer payé
- [ ] Mise à jour des commissions liées

---

### Phase 2: Interface utilisateur (Semaine 3-4) - 8 jours
**Objectif:** Wallet et dashboards

#### Jour 9-10: Wallet vendeur
- [ ] Menu "Mes Commissions"
- [ ] Vue liste avec filtres (payé/non payé)
- [ ] Vue formulaire détaillée (SO, facture, montants)
- [ ] Vue pivot/graph pour statistiques
- [ ] Droits d'accès (voir uniquement ses commissions)

#### Jour 11-12: Système de réclamation
- [ ] Créer `sale.commission.claim`
- [ ] Bouton "Réclamer" depuis wallet
- [ ] Notifications admins (email + activités)
- [ ] Actions admin: approuver/rejeter
- [ ] Notifications vendeur sur décision

#### Jour 13-14: Dashboard chef d'équipe
- [ ] Menu "Commissions Équipe"
- [ ] Vue hiérarchique (mes commissions + équipe)
- [ ] Rapport périodique
- [ ] Graphiques performance équipe

#### Jour 15-16: Dashboard admin
- [ ] Vue "Toutes les commissions"
- [ ] Filtres avancés (rôle, statut, période)
- [ ] Recherche par BC/vendeur/date
- [ ] Action batch "Préparer paiement"
- [ ] Vue récapitulative (pivot)

---

### Phase 3: Flexibilité et ajustements (Semaine 5) - 4 jours
**Objectif:** Gestion des exceptions

#### Jour 17-18: Ajustements manuels
- [ ] Créer `sale.commission.adjustment`
- [ ] Bouton "Ajuster" depuis formulaire commission
- [ ] Wizard ajustement avec raisons
- [ ] Historique des ajustements
- [ ] Modification % par vente spécifique

#### Jour 19: Annulation/Corrections
- [ ] Trigger annulation vente → annulation commissions
- [ ] Action "Annuler commission"
- [ ] Gestion commissions exceptionnelles (utiliser `sale.commission.achievement`)

#### Jour 20: Finalisation
- [ ] Tests d'intégration complets
- [ ] Documentation utilisateur
- [ ] Formation admin/vendeurs

---

### Phase 4: Sécurité et optimisation (Semaine 6) - 3 jours
**Objectif:** Droits et performance

#### Jour 21: Sécurité
- [ ] `ir.model.access` pour tous les modèles
- [ ] `ir.rule` pour isolation des données
- [ ] Groupe "Commission Manager"
- [ ] Tests droits d'accès

#### Jour 22: Optimisation
- [ ] Index sur champs recherchés (user_id, date, status)
- [ ] Optimisation requêtes (prefetch)
- [ ] Cache pour dashboards

#### Jour 23: Documentation
- [ ] Documentation technique (modèles, flux)
- [ ] Guide administrateur
- [ ] Guide utilisateur (vendeur/chef)

---

## 📊 Résumé des ressources

### Modèles à créer: 4
1. `hr.commission.role.config`
2. `sale.commission.payment`
3. `sale.commission.claim`
4. `sale.commission.adjustment`

### Modèles à étendre: 3
1. `sale.commission.report` (renommer → `sale.commission`)
2. `sale.commission.plan`
3. `res.users` + `hr.employee`

### Vues à créer: ~25
- Formulaires: 8
- Listes: 8
- Kanban: 3
- Pivot/Graph: 4
- Wizards: 2

### Logique métier: ~10 méthodes principales
- Calcul hiérarchique
- Triggers factures
- Gestion paiements
- Réclamations
- Ajustements

---

## 🎯 Estimation finale

| Phase | Durée | Complexité | Priorité |
|-------|-------|------------|----------|
| **Phase 1: Fondations** | 8 jours | ⭐⭐⭐⭐ | 🔴 CRITIQUE |
| **Phase 2: Interfaces** | 8 jours | ⭐⭐⭐ | 🔴 CRITIQUE |
| **Phase 3: Flexibilité** | 4 jours | ⭐⭐ | 🟡 IMPORTANT |
| **Phase 4: Sécurité** | 3 jours | ⭐⭐ | 🟡 IMPORTANT |
| **TOTAL** | **23 jours** | - | - |

**Note:** Estimation pour 1 développeur Odoo expérimenté

---

## ✅ Checklist de validation

### Fonctionnel
- [ ] Commission calculée pour vendeur + chef + directeur sur chaque vente
- [ ] % différent par rôle configurable
- [ ] Déclenchement uniquement si facture payée
- [ ] Statut payé/non payé géré
- [ ] Wallet vendeur avec détails et filtres
- [ ] Réclamation avec notification admin
- [ ] Dashboard chef d'équipe
- [ ] Tableau récapitulatif admin
- [ ] Ajustements manuels possibles
- [ ] Annulation si vente annulée

### Technique
- [ ] Tous les modèles créés/étendus
- [ ] Triggers fonctionnels
- [ ] Droits d'accès configurés
- [ ] Tests unitaires passés
- [ ] Performance optimisée
- [ ] Documentation complète

### UX
- [ ] Navigation intuitive
- [ ] Filtres et recherches performants
- [ ] Notifications claires
- [ ] Rapports lisibles
- [ ] Actions batch efficaces

---

**Conclusion:** L'intégration nécessite un développement custom conséquent (~23 jours), mais s'appuie intelligemment sur les modèles Odoo existants pour minimiser le code à créer. La structure proposée est évolutive et maintainable.
