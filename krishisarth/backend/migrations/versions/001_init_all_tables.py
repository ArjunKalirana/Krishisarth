"""init all tables

Revision ID: 001
Revises: 
Create Date: 2026-03-19 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Farmers
    op.create_table(
        'farmers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('preferred_lang', sa.String(), server_default='en', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_farmers_email', 'farmers', ['email'])

    # 2. Farms
    op.create_table(
        'farms',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lng', sa.Float(), nullable=True),
        sa.Column('area_ha', sa.Float(), nullable=True),
        sa.Column('soil_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['farmer_id'], ['farmers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_farms_farmer', 'farms', ['farmer_id'])

    # 3. Zones
    op.create_table(
        'zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('crop_type', sa.String(), nullable=False),
        sa.Column('crop_stage', sa.String(), nullable=True),
        sa.Column('area_sqm', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_zones_farm', 'zones', ['farm_id'])
    op.create_index('idx_zones_active', 'zones', ['farm_id'], postgresql_where=sa.text('is_active = true'))

    # 4. Devices
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('serial_no', sa.String(), nullable=False),
        sa.Column('firmware_ver', sa.String(), nullable=True),
        sa.Column('battery_pct', sa.Integer(), nullable=True),
        sa.Column('is_online', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_no')
    )
    op.create_index('idx_devices_zone', 'devices', ['zone_id'])
    op.create_index('idx_devices_serial', 'devices', ['serial_no'])

    # 5. AI Decisions
    op.create_table(
        'ai_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_type', sa.String(), nullable=False),
        sa.Column('reasoning', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('water_saved_l', sa.Float(), nullable=True),
        sa.Column('input_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_zone_time', 'ai_decisions', ['zone_id', sa.text('created_at DESC')])

    # 6. Irrigation Schedules
    op.create_table(
        'irrigation_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(), server_default='ai', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_min', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('celery_task_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_irr_pending', 'irrigation_schedules', ['scheduled_at'], postgresql_where=sa.text("status = 'pending'"))
    op.create_index('idx_irr_zone_time', 'irrigation_schedules', ['zone_id', sa.text('scheduled_at DESC')])

    # 7. Fertigation Logs
    op.create_table(
        'fertigation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nutrient_type', sa.String(), nullable=False),
        sa.Column('concentration_ml', sa.Float(), nullable=False),
        sa.Column('ec_before', sa.Float(), nullable=True),
        sa.Column('ec_after', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), server_default='completed', nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fert_zone_time', 'fertigation_logs', ['zone_id', sa.text('applied_at DESC')])

    # 8. Alerts
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alerts_unread', 'alerts', ['farm_id', sa.text('created_at DESC')], postgresql_where=sa.text('is_read = false'))
    op.create_index('idx_alerts_severity', 'alerts', ['farm_id', 'severity', sa.text('created_at DESC')])

def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('fertigation_logs')
    op.drop_table('irrigation_schedules')
    op.drop_table('ai_decisions')
    op.drop_table('devices')
    op.drop_table('zones')
    op.drop_table('farms')
    op.drop_table('farmers')
